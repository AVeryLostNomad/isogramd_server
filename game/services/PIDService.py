import random, string


class PIDService:

    def __init__(self, isogram_server):
        self.isogram_server = isogram_server
        self.player_ids = {} # Dict of player-id to actual player object

    @staticmethod
    def generate_id():
        random_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.ascii_letters + string.ascii_lowercase) for _ in range(25))
        return random_id

    def register_profile(self, profile):
        gen_key = PIDService.generate_id()
        while gen_key in self.player_ids.keys():
            gen_key = PIDService.generate_id()
        self.player_ids[gen_key] = profile
        return gen_key

    def get_profile_from_key(self, key):
        if key not in self.player_ids.keys():
            return None
        return self.player_ids[key]

    def terminate_pid_association_key(self, key=""):
        self.player_ids.pop(key, None)

    def terminate_pid_association_profile(self, profile):
        for entry in self.player_ids.keys():
            if self.player_ids[entry] == profile:
                self.player_ids.pop(entry, None)
                return
