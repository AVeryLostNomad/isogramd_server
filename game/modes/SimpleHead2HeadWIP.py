import game_util, math, time
from BaseGame import BaseGame
import numpy as np


class SimpleHead2Head(BaseGame):

    def __init__(self, match_service):
        self.initialize(match_service)

    def initialize(self, match_service, subsequent_load=False):
        self.match_service = match_service
        if subsequent_load:
            self.id = self.match_service.get_next_free_match_id()
        else:
            self.id = -1
        self.players = []
        self.player_pids = []
        self.should_tick = False

        self.move_id_by_player = {}
        self.move_log_by_player = {}

        self.selected_size = 5

        self.confirms_needed = 2
        self.confirms_obtained = 0

        self.game_start_time = {}
        self.game_end_time = {}

        self.ends_still_needed = 1

    def is_suitable_player(self, pid, context={}):
        player = self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid)
        if len(self.players) == 0:
            # No players are in this match yet
            # Thus anyone is a match
            return True
        else:
            distance = math.fabs(player.get_iiq() - self.players[0].get_iiq())
            if distance < 250:
                return True
            else:
                return False

    def get_queue_priority(self):
        return 100

    def get_desired_number_of_players(self, context={}):
        return 2

    def add_player(self, pid, context={}):
        self.move_id_by_player[pid] = 0
        player_obj = self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid)
        self.players.append(player_obj)
        self.player_pids.append(pid)

    def tick(self, tick_count):
        pass

    def other_player(self, test_player):
        for player in self.players:
            if player == test_player:
                continue
            if player.email == test_player.email:
                continue
            return player

    def other_pid(self, this_pid):
        for key in self.move_id_by_player.keys():
            if key == this_pid:
                continue
            return key

    def begin_game(self, context={}):
        self.confirms_obtained += 1

        if self.confirms_obtained != self.confirms_needed:
            player = self.match_service.isogram_server.get_pid_service().get_profile_from_key(context["player_id"])
            player.add_server_message("[WAIT]")
            player.add_server_message("Waiting for the other player to join...")
            return

        for player in self.players:
            other = self.other_player(player)
            player.add_server_message("You will be playing against " + other.get_email() + " who has an iiq of " +
                                      str(other.get_iiq()))
            player.add_server_message("Your time will be tracked individually, and iiq gain/loss will be based "
                                      "upon the degree to which you are victorious.")
            player.add_server_message("Your time begins when you make the first guess. Good luck!")
            player.add_server_message("[RELEASE]")

        self.target_word = self.match_service.isogram_server.get_word_db().get_word(self.selected_size, "commonautica")
        print("Selected word: " + self.target_word)

    def get_game_status(self):
        return_dict = {}
        for key in self.move_log_by_player.keys():
            # This player's move log.
            most_bulls = 0
            last_bulls = 0
            last_cows = 0
            this_player_dictionary = self.move_log_by_player[key]
            for movenum in this_player_dictionary.keys():
                move = this_player_dictionary[movenum]
                string_guess = move["guess"]
                bulls, cows = game_util.count_bulls_cows(self.target_word, string_guess)
                last_bulls = bulls
                last_cows = cows
                if bulls > most_bulls:
                    most_bulls = bulls
            this_player = {
                "most_bulls": most_bulls,
                "last_bulls": last_bulls,
                "last_cows": last_cows
            }
            return_dict[key] = this_player
        return return_dict


    def record_move(self, pid, move):
        if pid not in self.move_id_by_player.keys():
            self.move_id_by_player[pid] = 0
            self.move_log_by_player[pid] = {}
        self.move_id_by_player[pid] += 1
        move.player = self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid)
        bulls, cows = game_util.count_bulls_cows(move.guess, self.target_word)
        move.bulls = bulls
        move.cows = cows
        if pid not in self.move_log_by_player.keys():
            self.move_log_by_player[pid] = {}
        dict = self.move_log_by_player[pid]
        dict[self.move_id_by_player[pid]] = move.to_json()
        self.move_log_by_player[pid] = dict
        player = move.player

        if pid not in self.game_start_time.keys():
            # We already need to set game start time
            self.game_start_time[pid] = time.time()

        if move.guess == self.target_word:
            # They win! Track stuff and then end_game
            self.game_end_time[pid] = time.time()
            difference = self.game_end_time[pid] - self.game_start_time[pid]
            player.add_server_message("You guessed the word in " + str(difference) + " seconds.")

            if self.ends_still_needed == 0:
                player.add_server_message("You are the last player to finish, but you have not necessarily lost.")
                player.add_server_message("The game will be scored and the winner determined shortly.")
                player.add_server_message("[WAIT]")
                self.other_player(player).add_server_message("The other player has just finished.")
                self.end_game()
                return
            else:
                player.add_server_message("You are the first person to finish, but you have not necessarily won!")
                player.add_server_message("The game will be scored and the winner determined shortly.")
                player.add_server_message("[WAIT]")

            self.ends_still_needed -= 1
        else:
            # Show bulls and cows (also print the highest number of bulls and cows your enemy has registered,
            # plus the very last one)
            player.add_server_message("Bulls: " + str(bulls) + " and Cows: " + str(cows))
            other_pid = self.other_pid(pid)
            game_status = self.get_game_status()
            if other_pid not in game_status.keys():
                # Opponent has not guessed
                return
            other_players_moves = game_status[other_pid]
            player.add_server_message("Your opponent has identified " + str(other_players_moves["most_bulls"]) +
                                      " bulls.")
            player.add_server_message("Their last guess had " + str(other_players_moves["last_bulls"]) + " bulls and "
                                      + str(other_players_moves["last_cows"]) + " cows")

    def difference_in_player_times(self):
        least_time = 100000
        difference = 0
        for pid in self.player_pids:
            ptime = self.game_end_time[pid] - self.game_start_time[pid]
            if ptime < least_time:
                least_time = ptime
        for pid in self.player_pids:
            time = self.game_end_time[pid] - self.game_start_time[pid]
            if time == least_time:
                continue
            difference = time - least_time
        return difference, least_time

    def difference_in_player_moves(self):
        least_moves = 10000
        difference = 0
        for pid in self.player_pids:
            pmoves = self.move_id_by_player[pid]
            if pmoves < least_moves:
                least_moves = pmoves
        for pid in self.player_pids:
            pmoves = self.move_id_by_player[pid]
            if pmoves == least_moves:
                continue
            difference = pmoves - least_moves
        return difference, least_moves

    # Magic numbers applenty, but this was the most well fit function to my guesstimated reward values
    @staticmethod
    def time_reward_function(time_difference):
        return (4806.8650485745911 * np.sinc(4.4358303100191581 * np.pi * time_difference)) + (
        0.032158790024453009 * np.pi * time_difference) + 25.347387598313965

    @staticmethod
    def move_reward_function(move_difference):
        return round((1.6616222760304988 * move_difference) + -1.8069007263983736, 0)

    def end_game(self, context={}):
        time_difference, least_time = self.difference_in_player_times()
        move_difference, least_moves = self.difference_in_player_moves()

        for pid in self.player_pids:
            player = self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid)
            ptime = self.game_end_time[pid] - self.game_start_time[pid]
            pmoves = self.move_id_by_player[pid]

            player_points = 0
            player.add_server_message("\n")
            time_reward = SimpleHead2Head.time_reward_function(time_difference)
            print("Time reward", time_reward, "Time difference", time_difference)
            if time_reward > 80:
                time_reward = 80
            if time_reward < 0:
                time_reward = 0
            if ptime == least_time:
                player.add_server_message("You were " + str(time_difference) + " seconds faster than your opponent!")
                player_points += time_reward
            else:
                player.add_server_message("You were " + str(time_difference) + " seconds slower than your opponent.")
                time_reward *= -1
                player_points += time_reward

            move_reward = SimpleHead2Head.move_reward_function(move_difference)
            print("Move reward", move_reward)
            if move_reward > 50:
                move_reward = 50
            if move_reward < 0:
                move_reward = 0
            if pmoves == least_moves:
                player.add_server_message("You finished " + str(move_difference) + " moves before your opponent!")
                player_points += move_reward
            else:
                player.add_server_message("You finished " + str(move_difference) + " moves after your opponent.")
                move_reward *= -1
                player_points += move_reward

            self.iiq_change = player_points

            if player_points > 0:
                player.set_iiq(player.get_iiq() + player_points)
                self.match_service.isogram_server.get_account_service().save()
                player.add_server_message("You won, and your iiq has been increased to " + str(player.get_iiq()))
                player.add_server_message("Good game! See you next time!")
                player.add_server_message("[RELEASE]")
            else:
                player.set_iiq(player.get_iiq() + player_points)
                self.match_service.isogram_server.get_account_service().save()
                player.add_server_message("You lost, and your iiq has dropped to " + str(player.get_iiq()))
                player.add_server_message("Good game! See you next time!")
                player.add_server_message("[RELEASE]")

            self.match_service.pop_game(self.id)

    def get_loggable(self):
        pass

    def is_player_involved(self, profile):
        # Is this player involved in this game?
        pass




