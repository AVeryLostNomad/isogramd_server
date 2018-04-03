from abc import ABCMeta, abstractmethod


class BaseReward:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def award_player(self, player):
        # Receiving a player object, credit this player somehow.
        pass
