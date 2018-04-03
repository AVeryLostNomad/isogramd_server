import game_util
import math
import time

from BaseGame import BaseGame


class Placements(BaseGame):

    def __init__(self, match_service):
        self.initialize(match_service)

    def initialize(self, match_service, subsequent_load=False):
        self.match_service = match_service
        if subsequent_load:
            self.id = self.match_service.get_next_free_match_id()
        else:
            self.id = -1
        self.players = []
        self.should_tick = False

        self.move_id = 0
        self.move_log = {}

        self.game_start_time = time.time()

        self.current_size = 5
        self.current_phase = 0
        self.phases = {}

        self.targets = {
            3: 300,
            4: 400,
            5: 450,
            6: 500,
            7: 600,
            8: 700
        }

        self.estimation = 2500
        self.confidence = 0

        self.confirms_needed = 1
        self.confirms_obtained = 0

    # Only players with no iiq placement may queue in placement matches
    def is_suitable_player(self, pid, context={}):
        player = self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid)
        if player.get_iiq() != 0:
            return False
        return True

    def get_queue_priority(self):
        return 10001

    def get_desired_number_of_players(self, context={}):
        return 1

    def add_player(self, pid, context={}):
        self.players.append(self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid))

    def tick(self, tick_count):
        pass

    def begin_game(self, context={}):

        self.confirms_obtained += 1

        if self.confirms_obtained != self.confirms_needed:
            return

        self.players[0].add_server_message("Welcome to your placement matches!")
        self.players[0].add_server_message("You will be provided with a series of challenges. These will take approximately 30 minutes, but potentially as long as an hour, depending on how difficult you are to judge.")
        self.players[0].add_server_message("Placement matches cannot be paused and resumed, and *are* time sensitive. If you are not ready for that time commitment, please ': exit' now. ")

        self.players[0].add_server_message("\nYour first word will be a five letter isogram. Can you do it in seven and a half minutes?")
        self.players[0].add_server_message("Time starts the very instant your first guess is received by the server. Good luck!")

        self.target_word = self.match_service.isogram_server.get_word_db().get_word(5, "commonautica")

    def phase_depth_function(self, current_phase):
        if current_phase >= 1:
            return (math.pi * current_phase * 27.6) + (56 * (current_phase + 1))
        else:
            return (math.pi * current_phase * 27.6) + 56

    def record_move(self, pid, move):
        self.move_id += 1
        move.player = self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid)
        self.move_log[self.move_id] = move.to_json()

        if self.current_phase not in self.phases.keys():
            # Start the clock.
            self.phases[self.current_phase] = {
                "size": self.current_size,
                "time_start": time.time(),
                "time_end": -1,
                "target_word": self.target_word
            }

        if move.guess == self.target_word:
            # They got this phase right. Record time and decide if / what we need to do for the next phase
            now_time = time.time()
            self.phases[self.current_phase]["time_end"] = now_time
            your_time = now_time - self.phases[self.current_phase]["time_start"]
            goal = self.targets[self.current_size]

            denominator = (math.fabs(goal - your_time)) - self.phase_depth_function(self.current_phase)
            if denominator <= 1:
                denominator = 1
            self.confidence = 1 / denominator

            multiples = {
                0: 0.86,
                1: 0.50,
                2: 0.36,
                3: 0.25,
                4: 0.11,
                5: 0
            }

            p_diff = ((goal - your_time) / ((goal + your_time) / 2))
            rough_change = (self.estimation * p_diff) * multiples[self.current_phase]

            if rough_change >= 0:
                self.phases[self.current_phase]["win"] = True,
            else:
                self.phases[self.current_phase]["win"] = False

            self.estimation = self.estimation + rough_change

            self.players[0].add_server_message("Well done! You answered correctly. That took you " + str(your_time) +
                                               " seconds")
            if self.confidence >= 0.85:
                # We are done.
                self.end_game()
                return
            else:
                # That wasn't precise enough. Do another!
                self.current_phase += 1

                if self.current_phase == 1:
                    # This is the second one.
                    if self.phases[self.current_phase - 1]["win"]:
                        self.current_size += 2
                    else:
                        self.current_size -= 2
                else:
                    if self.phases[self.current_phase - 1]["win"]:
                        self.current_size += 1
                    else:
                        self.current_size -= 1

                if self.current_size < 3:
                    self.current_size = 3

                if self.current_size > 8:
                    self.current_size = 8

                self.players[0].add_server_message("Unfortunately, the placement engine is not convinced of your iiq "
                                                   "just yet.")
                self.players[0].add_server_message("You'll need to do another. This time a " + str(self.current_size) +
                                                   "-gram in " + str(self.targets[self.current_size]) + ".")
                self.players[0].add_server_message("As before, time starts when you make your first guess. Good luck!")
                self.target_word = self.match_service.isogram_server.get_word_db().get_word(self.current_size, "commonautica")

        if not game_util.is_isogram(move.guess):
            self.players[0].add_server_message("That's not an isogram! (But we did count it for your time)")
            return
        if len(move.guess) != self.current_size:
            self.players[0].add_server_message("That word is only " + str(len(move.guess)) + " letters long, but you're guessing for a " + str(self.current_size))
            return

        bulls, cows = game_util.count_bulls_cows(self.target_word, move.guess)
        self.players[0].add_server_message("Bulls: " + str(bulls) + " and Cows: " + str(cows))

    def end_game(self, context={}):
        self.is_finished = True
        self.players[0].add_server_message("Placements finished!")
        self.game_end_time = time.time()
        time_difference = self.game_end_time - self.game_start_time
        self.players[0].add_server_message(
            "You did that in " + str(time_difference) + " seconds and " + str(self.move_id - 1) + " moves total")
        self.players[0].add_server_message("And your ending iiq is: " + str(self.estimation))
        self.players[0].add_server_message("Enjoy the game, and good luck!")
        if self.estimation > 5000:
            self.estimation = 5000
        if self.estimation < 0:
            self.estimation = 0
        self.players[0].iiq = self.estimation
        self.match_service.isogram_server.get_stat_service().record_game(self)
        self.match_service.isogram_server.get_stat_service().save()
        self.match_service.pop_game(self.id)

    def get_loggable(self):
        # We don't want to log placement matches in a player's stats, so we merely pass here.
        pass

    def is_player_involved(self):
        pass




