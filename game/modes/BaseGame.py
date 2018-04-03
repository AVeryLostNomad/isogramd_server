from abc import ABCMeta, abstractmethod, abstractproperty


class Move:

    def __init__(self):
        # Sent by sender
        self.game_id = ""
        self.guess = ""
        self.timestamp = ""

        self.bulls = 0
        self.cows = 0

        # Strapped in on receipt
        self.player = None

    def from_json(self, json_text):
        self.game_id = json_text["game_id"]
        self.guess = json_text["guess"]
        self.timestamp = json_text["timestamp"]

    def to_json(self):
        return_json = {
            "game_id" : self.game_id,
            "guess": self.guess,
            "timestamp": self.timestamp,
            "player": self.player.to_json(hide_personal_details=True)
        }
        return return_json


# Template for game modes. Provides a compatibility layer for win conditions, etc...
class BaseGame:
    __metaclass__ = ABCMeta

    def __init__(self, isogram_server):
        self.isogram_server = isogram_server
        self.id = self.isogram_server.get_match_service().get_next_free_match_id()
        self.is_finished = False

    @abstractmethod
    def get_queue_priority(self):
        # Some gamemodes should take preference over others. E.g. placements
        # Higher the number, more priority.
        pass

    @abstractmethod
    def get_name(self):
        # Get a name of this gamemode
        pass

    @abstractmethod
    def get_description(self):
        # Get a description of this gamemode
        pass

    @abstractmethod
    def get_desired_number_of_players(self, context={}):
        # How many players are needed for this gamemode?
        pass

    @abstractmethod
    def is_suitable_player(self, pid, context={}):
        # Method to check other players for this game.
        # Could be used to do things like check if the other player wants this type of game, if they're in the same
        # team, etc..
        pass

    @abstractmethod
    def add_player(self, pid, context={}):
        # Add a player to this game
        pass

    @abstractmethod
    def begin_game(self, context={}):
        # Argument 'context' contains things like the IPs of players connecting (maybe for geolocation time-zone
        # mapping? which could be useful for more advanced multi-day gamemodes? Give players a break at earliest
        # convenience?)

        # More arguments can be added as necessary
        pass

    @abstractmethod
    def end_game(self, context={}):
        # Same as above
        # This time, end the game
        # Do things like anti-cheat validation, etc...
        # Then, after all of that, announce that the game is finish and handle iiq changes
        # Finally, wrap up the termination of this game object and go from there
        pass

    @abstractmethod
    def record_move(self, pid, move):
        # Check the move against this mode's conditions
        pass

    @abstractmethod
    def is_player_involved(self, profile):
        # Is this player involved in this game?
        pass

    @abstractmethod
    def get_opponents(self, profile):
        # Get the other players involved in this game, as a list of profiles
        pass

    @abstractmethod
    def tick(self, tick_count):
        # Handle normal functions like checking turn progression and all
        # Only called if self.should_tick is True
        pass

    @abstractmethod
    def get_loggable(self):
        # Return a list of log instructions (tuples) of form (n-gram-size, player, time spent, won/lost)
        pass

    @abstractmethod
    def pregame(self, result=""):
        # Return either a list containing the elements that need to be filled in before the game, or, if
        # result is filled in, set those elements.
        pass

