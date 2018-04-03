import json


class Theme:

    # These sorts of things need to be specified in this class
    def __init__(self):
        self.wall_design = 0

    def from_json(self, json_text):
        self.wall_design = json_text["wall_design"]

    def to_json(self):
        return_json = {
            "wall_design": self.wall_design
        }
        return return_json

