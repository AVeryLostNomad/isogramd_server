

class RewardService:

    def __init__(self, isogram_server):
        self.isogram_server = isogram_server
        self.pending_rewards = {}  # Dictionary of rewards by username
        pass

    def add_reward(self, username, grams, scoins):
        self.pending_rewards[username] = {
            "grams": grams,
            "scoins": scoins
        }

    def get_reward(self, username):
        if username in self.pending_rewards.keys():
            return self.pending_rewards[username]
        return {
            "grams": 0,
            "scoins": 0
        }

    def clear_reward(self, username):
        if username in self.pending_rewards.keys():
            self.pending_rewards.pop(username, None)