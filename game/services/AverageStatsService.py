import os, json
from Practice import Practice
from SimpleHead2HeadWIP import SimpleHead2Head

class AverageStatsService:

    def __init__(self, isogram_server):
        self.isogram_server = isogram_server
        self.file_path = self.isogram_server.get_server_configuration().file_base + "stats.json"
        self.highest_game_id = 0
        self.games_to_add = []
        self.json_content = {}

        if os.path.isfile(self.file_path):
            self.load()
        else:
            # Create a new one
            open(self.file_path, "w+")  # Create the new file
            self.save()

    def to_json(self):
        for game in self.games_to_add:
            if isinstance(game, Practice):
                self.json_content[game.id] = {
                    "involved_players": [x.to_json(hide_personal_details=True) for x in game.players],
                    "move_count": game.move_id,
                    "move_log": game.move_log,
                    "n_gram_size": game.n_gram_size,
                    "target_word": game.target_word,
                    "start_time": game.game_start_time,
                    "end_time": game.game_end_time
                }
            if isinstance(game, SimpleHead2Head):
                sub_json = {}
                for pid in game.player_pids:
                    sub_json[pid] = {
                        "player_object": self.isogram_server.get_pid_service().get_profile_from_key(pid).to_json(hide_personal_details=True),
                        "player_move_count": game.move_id_by_player[pid],
                        "player_move_log": game.move_log_by_player[pid],
                        "player_start_time": game.game_start_time[pid],
                        "player_end_time": game.game_end_time[pid]
                    }
                self.json_content[game.id] = {
                    "involved_players": [x.to_json(hide_personal_details=True) for x in game.players],
                    "target_word": game.target_word,
                    "n_gram_size": len(game.target_word),
                    "iiq_change": game.iiq_change,
                    "player_stats": sub_json
                }
        self.games_to_add = []
        return self.json_content

    def get_highest_game_id(self):
        return self.highest_game_id

    def record_game(self, game):
        if game.id > self.highest_game_id:
            self.highest_game_id = game.id
        self.games_to_add.append(game)
        self.save()

    def from_json(self, json_text):
        for key in json_text.keys():
            if int(key) > self.highest_game_id:
                self.highest_game_id = int(key)

        self.json_content = json_text

    def load(self):
        with open(self.file_path) as data_file:
            json_text = json.load(data_file)
        self.from_json(json_text)

    def save(self):
        with open(self.file_path, 'w') as data_file:
            json.dump(self.to_json(), data_file)

