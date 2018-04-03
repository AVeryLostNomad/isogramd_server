from abc import ABCMeta, abstractmethod


class BaseQuest:
    __metaclass__ = ABCMeta
    # Quests will have to be serializable, so as to permit saving and loading player quests in case of server
    # restart

    # Default quest initializer. Pass in a quest template (a quest object) from the quest service to copy basic
    # values from that
    def __init__(self, quest_template=None):
        self.name = ""
        self.assigning_npc_id = -1
        self.reward = None
        self.do_tick = False

    @abstractmethod
    def quest_conditions_met_by_game(self, game):
        # Returns simply whether a game that is finished by the player meets the conditions of this quest.
        # Will be passed every game upon completion and the calling of the end_game method
        # Will also be passed games upon start of the game. Status of the game may be checked with the game.is_finished
        # flag.
        pass

    @abstractmethod
    def quest_conditions_met_by_state(self, player):
        # Returns whether the player currently meets the conditions of this quest's completion. Could be used
        # to see whether the player has equipped a specific item, or perhaps whether the player is queuing, etc...
        # Called from the QuestService's tick if self.do_tick is True
        pass
