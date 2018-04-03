import game_util
import time
import json

from BaseGame import BaseGame


class Practice(BaseGame):

    def __init__(self, match_service):
        self.initialize(match_service)

    def initialize(self, match_service, subsequent_load=False):
        self.match_service = match_service
        if subsequent_load:
            self.id = self.match_service.get_next_free_match_id()
        else:
            self.id = -1
        self.players = []  # Until we have added players, this must remain empty
        self.should_tick = False

        self.move_id = 0
        self.move_log = {}

        self.n_gram_size = -1
        self.target_word = ""

        self.game_start_time = -1

        self.confirms_needed = 1
        self.confirms_obtained = 0

        self.perfect_victory = True

        self.pregame_done = False

    def is_suitable_player(self, pid, context={}):
        return True  # Everyone is permitted to practice.

    def get_opponents(self, profile):
        opponent_list = []
        for prof in self.players:
            if prof == profile:
                continue
            opponent_list.append(prof)
        return opponent_list

    def get_desired_number_of_players(self, context={}):
        return 1  # There could theoretically be a two person practice mode in the future. Or a 6 person, etc...

    def get_queue_priority(self):
        return 10000  # Highest priority to solo practice. Maybe TODO replace this with a queue service?

    def add_player(self, pid, context={}):
        self.players.append(self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid))

    def begin_game(self, context={}):
        # How many letters should appear in our n-gram? Good question.
        # This method is called when each player receives game ID, and it incremements self.confirms_obtained

        self.confirms_obtained += 1

        if self.confirms_obtained != self.confirms_needed:
            # Can only begin the game once all players have confirmed their knowledge of the game. In this case,
            # one player.
            return

    # Recording a move will add it to the game object, increment different progressions, perhaps, notify other players
    # and the player sender, and check win conditions (to end the game or continue with a new word!)
    def record_move(self, pid, move):
        if not self.pregame_done:
            return
        self.move_id += 1
        move.player = self.match_service.isogram_server.get_pid_service().get_profile_from_key(pid)
        self.move_log[self.move_id] = move.to_json()

        if self.game_start_time == -1:
            self.game_start_time = time.time()

        # The game is afoot. Track this move and report bulls/cows count
        if move.guess == self.target_word:
            # In this case, they win. In future games, this could be one point to one team and then a restart,
            # or even something else entirely!
            self.end_game()
            return

        bulls, cows = game_util.count_bulls_cows(self.target_word, move.guess)
        if bulls == 0 and cows == 0:
            self.perfect_victory = False
        move.player.add_server_message(({
            "bulls": bulls,
            "cows": cows
        }), is_json=True)

    def end_game(self, context={}):
        self.is_finished = True
        self.game_end_time = time.time()
        time_difference = self.game_end_time - self.game_start_time
        send_json = {
            "game_end": 1,
        }
        self.players[0].add_server_message(send_json, is_json=True)

        self.players[0].add_postgame_message("You win!", is_json=False)
        self.players[0].add_postgame_message("You did that in " + str(time_difference) + " seconds", is_json=False)
        self.players[0].add_postgame_message("You did that in " + str(self.move_id) + " moves", is_json=False)
        self.players[0].add_postgame_message("Because this was practice, no iiq or currency change will happen.", is_json=False)
        self.players[0].add_postgame_message("[DONE_BUTTON]", is_json=False)
        self.match_service.pop_game(self.id)

    def is_player_involved(self, profile):
        return self.players[0] == profile

    def tick(self, tick_count):
        pass

    def get_loggable(self):
        # We won't count practice matches as to win/loss ratio, but we will let it factor into average time.
        # It will be counted a perfect victory if this was one
        p_vic = 0
        if self.perfect_victory:
            p_vic = 1
        return [(self.n_gram_size, self.players[0], self.game_end_time - self.game_start_time, self.move_id, -1,
                 p_vic)]

    def get_name(self):
        return "Practice"

    def get_description(self):
        return "Challenge yourself and try to get better!"

    def pregame(self, result=""):
        if result == "":
            return {
                "n_gram_size":{
                    "title": "Desired N-Gram Size",
                    "description": "How large of an n-gram would you like to practice?",
                    "type": "text_field",
                    "attributes": {
                        "length": "1",
                        "allowed_char_types": "Integer",
                        "allowed_values": game_util.strange_inclusive(3, 11)
                    }
                }
            }
        else:
            #We received back what we asked for.
            result_dict = json.loads(result)
            self.n_gram_size = int(result_dict["n_gram_size"])
            json_array = {
                "word_size": str(self.n_gram_size)
            }
            self.players[0].add_server_message(json_array, is_json=True)
            self.target_word = self.match_service.isogram_server.get_word_db().get_word(self.n_gram_size, "commonautica")
            print(self.target_word)
            self.players[0].add_server_message("[RELEASE]")  # Allow the player to continue on to the game
            self.pregame_done = True



