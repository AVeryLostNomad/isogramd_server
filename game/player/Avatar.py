import json

class Avatar:

    def __init__(self):
        self.skin_tone = 0x000000
        self.head = 0  # Head number zero
        self.hair = 0  # Hair number zero
        self.eyes = 0
        self.ears = 0
        self.mouth = 0
        self.nose = 0

        self.accessories = []
        self.amt_accessory = 4

        self.shirt = 0
        self.pants = 0
        self.shoes = 0

    def to_json(self):
        json_return = {
            "skin": self.skin_tone,
            "head": self.head,
            "hair": self.hair,
            "eyes": self.eyes,
            "ears": self.ears,
            "mouth": self.mouth,
            "nose": self.nose,
            "accessories": self.accessories,
            "accessories_amount": self.amt_accessory,
            "shirt": self.shirt,
            "pants": self.pants,
            "shoes": self.shoes
        }
        return json_return

    def from_json(self, json_text):
        self.skin_tone = json_text["skin"]
        self.head = json_text["head"]
        self.hair = json_text["hair"]
        self.eyes = json_text["eyes"]
        self.ears = json_text["ears"]
        self.mouth = json_text["mouth"]
        self.nose = json_text["nose"]
        self.accessories = json_text["accessories"]
        self.amt_accessory = json_text["accessories_amount"]
        self.shirt = json_text["shirt"]
        self.pants = json_text["pants"]
        self.shoes = json_text["shoes"]