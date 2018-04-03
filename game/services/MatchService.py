from BaseGame import BaseGame
import copy, time, json
from Practice import Practice
from PlacementsWIP import Placements
from SimpleHead2HeadWIP import SimpleHead2Head

class MatchService:

    # Unlike other services on the server, when the server is closed, all active games should immediately end
    # Thus, this one has no file - at least currently. If I think of a reason to add one, I will do so.
    def __init__(self, isogram_server):
        self.isogram_server = isogram_server
        self.looking_for_match = {}  # Dict of players looking for games. Set up

        self.match_id = self.isogram_server.get_stat_service().get_highest_game_id()

        self.match_types = {
            "practice": Practice(self),
           # "head2head": SimpleHead2Head(self)
        }

        self.average_queue_times = {}  # When someone joins the queue, we track them in looking for match
        self.guesstimated_wait_times = {}  # When someone joins the queue, we will try to provide them with an estimated wait time.
        self.banned_queue = {}  # Dictionary tracking profile username and then dictionary values. Each one has a timestamp banned.

        self.matches = []  # List of BaseGame objects

    def get_queue_priority(self, game_string):
        return self.match_types[game_string].get_queue_priority()

    def get_matches(self):
        return self.matches

    def tick(self, tick_count):
        #  Go through all users in the looking for match.
        print("Ticking " + str(len(self.matches)) + " games and " + str(len(self.looking_for_match.keys())) + " players")
        for game in self.matches:
            if game.should_tick:
                game.tick()
        for pid in self.looking_for_match.keys():
            if pid not in self.looking_for_match.keys():
                # This player just got placed in some other match. Nice
                continue
            profile = self.looking_for_match[pid]["profile"]
            desired_matches = self.looking_for_match[pid]["desired_matches"]
            sorted_matches = sorted(desired_matches, key=self.get_queue_priority)
            sorted_matches = self.filter_out_bad(profile, sorted_matches)

            if len(sorted_matches) == 0:
                self.looking_for_match.pop(pid, None)
                profile.add_server_message("[CANNOT_QUEUE]")
                continue

            match_found = False

            # New match loop
            for match_type in sorted_matches:
                # This is the most preferred match type for this player
                # Let's see if they can do it and/or if we can find someone else to do it with them.
                game_setup = copy.deepcopy(self.match_types[match_type])
                # Maybe is an instance copy of the type of game-mode we want to play?

                if not game_setup.is_suitable_player(pid):
                    continue
                # This match type works for this player, can we find other ones that it works for?

                temp_players = []

                temp_players.append(pid)

                start_time = time.time()
                while (len(temp_players) != game_setup.get_desired_number_of_players()) and ((time.time() - start_time)
                                                                                                 < 30):
                    for spid in self.looking_for_match.keys():
                        if spid == pid:
                            # this is the same person
                            continue
                        sprofile = self.looking_for_match[spid]["profile"]
                        sdesired_matches = self.looking_for_match[spid]["desired_matches"]
                        if match_type in sdesired_matches:
                            # Go ahead and add this player!
                            temp_players.append(spid)

                            if str(spid) in self.guesstimated_wait_times.keys():
                                self.guesstimated_wait_times.pop(str(spid))
                            break

                if len(temp_players) != game_setup.get_desired_number_of_players():
                    # Could not make game. Ignore attempt and continue on
                    continue

                # Hey! We found enough players! Very cool!
                print("Both players have been held in a queue to join the same game! Nice!")
                match_found = True

                if str(pid) in self.guesstimated_wait_times.keys():
                    self.guesstimated_wait_times.pop(str(pid))

                game_setup.initialize(self.isogram_server.get_match_service(), subsequent_load=True)

                for player_id in temp_players:
                    print("Adding this player")
                    game_setup.add_player(player_id)
                    print("This player has PID " + str(player_id))
                    context = {
                        "player_id": player_id
                    }
                    game_setup.begin_game(context=context)
                    print("Game finished beginning", game_setup.id)
                    profile = self.isogram_server.get_pid_service().get_profile_from_key(player_id)
                    json_array = {
                        "game_id": game_setup.id
                    }
                    if hasattr(game_setup, 'selected_size'):
                        json_array["word_size", game_setup.selected_size]
                    profile.add_server_message(json_array, is_json=True)

                    time_started = self.looking_for_match[str(player_id)]["initial_queue"]
                    time_now = time.time()
                    ntotal_queued = 1
                    ntime_taken = time_now - time_started
                    if match_type in self.average_queue_times.keys():
                        ntotal_queued = self.average_queue_times[match_type]["total_queued"] + 1
                        ntime_taken = self.average_queue_times[match_type]["total_time_taken"] + (time_now - time_started)
                    self.average_queue_times[match_type] = {
                        "total_queued": ntotal_queued,
                        "total_time_taken": ntime_taken,
                        "average_wait": ntime_taken / ntotal_queued
                    }

                    self.looking_for_match.pop(player_id, None)  # Remove from the queue since they just found a game
                self.matches.append(game_setup)

            if match_found:
                continue
            # Unfortunately, if we reach this point, this player cannot be put into any games at this time.
            # Let's try another player, but first we should let this player know what's going on
            now_time = time.time()
            time_elapsed = now_time - self.looking_for_match[str(pid)]["initial_queue"]
            send_json = {
                "elapsed_seconds": time_elapsed,
            }
            wait_estimate = self.get_expected_wait_time(sorted_matches)  # Gets a current wait estimate
            previous = self.get_previous_wait_estimate(pid)
            if previous != -1:
                # If we have a previous wait estimate, we're going with that one
                wait_estimate = previous
            if wait_estimate != -1:
                # We have a guesstimate for wait time
                send_json["wait_seconds"] = wait_estimate
            if(time_elapsed > wait_estimate):
                # The player has waited longer than their wait estimate...
                # TODO maybe have some way of basing this off of the most popular queue types.
                # TODO should a player get rewarded for a long queue the same if they intentionally chose a less popular mode?
                if (time_elapsed) >= (10 * 60):
                    # More than 10 minutes spent in queue
                    send_json["drop_queue"] = True  # drop the queue.
                    # TODO maybe send more information here? Like, some dropped queues may have longer cooldowns than
                    # TODO others? Some may go ahead and give the reward, others drop it?
                    self.looking_for_match.pop(pid, None)  # Remove the player from this queue.
                    profile.distribute_marques(len(desired_matches))  # Distribute marques equivalent to the number of gamemodes this person could not be queued for
                    queue_ban = {}

                    for matcht in desired_matches:
                        queue_ban[matcht] = time.time()

                    self.banned_queue[profile.get_account_name()] = queue_ban
                else:
                    grams, starcoin = self.tabulate_reward(wait_estimate, time_elapsed)
                    send_json["reward"] = {
                        "grams": grams,
                        "starcoin": starcoin
                    }
                    self.isogram_server.get_reward_service().clear_reward(profile.get_account_name())
                    self.isogram_server.get_reward_service().add_reward(profile.get_account_name(), grams, starcoin)

            profile.add_server_message(send_json, is_json=True)

    def filter_out_bad(self, profile, sorted_matches):
        new_list = []
        for match in sorted_matches:
            # Match we're looking for
            found = False
            if profile.get_account_name() in self.banned_queue.keys():
                # Player is banned from certain matches
                for item in self.banned_queue[profile.get_account_name()].keys():
                    # Go through each type the player is banned from
                    if item == match:
                        # These are the same match type.
                        time_banned = self.banned_queue[profile.get_account_name()][item]
                        time_now = time.time()

                        if (time_now - time_banned) > (10 * 60):
                            # It's been longer than 10 minutes, we can go ahead and queue here.
                            new_list.append(item)
                        found = True
            if not found:
                new_list.append(match)
        return new_list

    def tabulate_reward(self, estimated_wait, actual_wait):
        # Both of these measurements are in seconds
        int_times_over = int(actual_wait / estimated_wait)
        starcoins = int_times_over * 10

        grams = ((actual_wait / estimated_wait) - int(actual_wait / estimated_wait)) * 250

        return grams, starcoins

    def get_next_free_match_id(self):
        self.match_id += 1
        return self.match_id

    def get_previous_wait_estimate(self, pid):
        if str(pid) in self.guesstimated_wait_times.keys():
            return self.guesstimated_wait_times[str(pid)]
        else:
            return -1

    def get_expected_wait_time(self, matches):
        shortest = 2000000
        for match in matches:
            if match in self.average_queue_times.keys():
                average = self.average_queue_times[match]["average_wait"]
                if average < shortest:
                    shortest = average
        if shortest == 2000000:
            return -1
        return shortest

    def get_game_from_gameid(self, game_id):
        for entry in self.matches:
            if str(entry.id) == str(game_id):
                return entry
        return None

    def gamemode_exists(self, match_types):
        for match_type_string in match_types:
            if match_type_string not in self.match_types.keys():
                return False
        return True

    def pop_game(self, game_id, do_record=True):
        for game in self.matches:
            if game.id == game_id:
                if do_record:
                    self.isogram_server.get_stat_service().record_game(game)
                    self.isogram_server.get_stat_service().save()
                    # We need to log these for the players.
                    for (n_gram_size, player, time_spent, moves, win_loss, perfect_victory) in game.get_loggable():
                        total_time_dict = player.get_total_play_time_by_size()
                        total_games_by_size = player.get_total_games_by_size()
                        total_moves_by_size = player.get_total_moves_by_size()

                        total_time_dict[str(n_gram_size)] += time_spent
                        total_games_by_size[str(n_gram_size)] += 1
                        total_moves_by_size[str(n_gram_size)] += moves

                        player.set_total_play_time_by_size(total_time_dict)
                        player.set_total_games_by_size(total_games_by_size)
                        player.set_total_moves_by_size(total_moves_by_size)

                        if win_loss == -1:
                            # Ignore this. The win/loss wasn't counted.
                            pass
                        elif win_loss == 1:
                            # It was a win
                            player.set_wins_total(player.get_wins_total() + 1)

                            if player.get_loss_streak() != 0:
                                # They were on a losing streak, but have now won. Set this to zero
                                last_loss_streak = player.get_loss_streak()
                                if last_loss_streak > player.get_largest_loss_streak():
                                    player.set_largest_loss_streak(last_loss_streak)

                                player.set_loss_streak(0)

                            player.set_win_streak(player.get_win_streak() + 1)
                        elif win_loss == 0:
                            # It was a loss
                            player.set_losses_total(player.get_losses_total() + 1)

                            if player.get_win_streak() != 0:
                                # They were on a winning streak, but have now won. Set this to zero
                                last_win_streak = player.get_win_streak()
                                if last_win_streak > player.get_largest_win_streak():
                                    player.set_largest_win_streak(last_win_streak)

                                player.set_win_streak(0)

                            player.set_loss_streak(player.get_loss_streak() + 1)

                        if player.get_losses_total() == 0:
                            player.set_win_loss_ratio(player.get_wins_total() / 1)
                        else:
                            player.set_win_loss_ratio(player.get_wins_total() / player.get_losses_total())

                        if perfect_victory == 1:
                            # This was a perfect victory
                            player.set_perfect_victories(player.get_perfect_victories() + 1)

                        queue_rewards = self.isogram_server.get_reward_service().get_reward(player.get_account_name())
                        player.set_grams(player.get_grams() + queue_rewards["grams"])
                        player.set_scoins(player.get_scoins() + queue_rewards["scoins"])

                    self.isogram_server.get_account_service().save()

                self.matches.remove(game)
                return

    def queue_for_match(self, pid, match_types):
        if not self.gamemode_exists(match_types):
            return False
        profile = self.isogram_server.get_pid_service().get_profile_from_key(pid)
        profile.clear_pending_messages()
        self.looking_for_match[str(pid)] = {
            "profile": profile,
            "desired_matches": match_types,
            "initial_queue": time.time()
        }
        estimated_wait = self.get_expected_wait_time(match_types)
        # If we are providing an estimated wait time here, then that needs to be law, by our terms.
        if estimated_wait != -1:
            profile.add_server_message({
                "wait_seconds": estimated_wait
            }, is_json=True)
            self.guesstimated_wait_times[str(pid)] = estimated_wait

        latest_ban = 0
        if profile.get_account_name() in self.banned_queue.keys():
            for item in self.banned_queue[profile.get_account_name()].keys():
                time_banned = self.banned_queue[profile.get_account_name()][item]
                if time_banned > latest_ban:
                    latest_ban = time_banned
        time_now = time.time()

        if (time_now - latest_ban) > (10 * 60):
            self.banned_queue.pop(profile.get_account_name(), None)

        self.isogram_server.get_reward_service().clear_reward(profile.get_account_name())


