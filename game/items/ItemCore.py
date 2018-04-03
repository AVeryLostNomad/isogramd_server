

# Class to hold item templates
class DefaultTemplates:

    def __init__(self):
        pass

    @staticmethod
    def get_lucky_tiki():
        template = ItemTemplate()
        template.name = "Lucky Tiki"
        template.max_items = 1
        template.consume_on_use = 1
        template.usable = 1
        template.sort_priority = 10
        template.image = "tiki.jpg"
        template.on_use = {
            "award_currency": {
                "type": "grams",
                "amount": 100
            }
        }
        template.rarity = 3
        template.discardable = 0
        return template


# Class to hold item use methods
class ItemUses:

    def __init__(self):
        pass

    @staticmethod
    def award_currency(profile, metadata):
        amount = metadata["amount"]
        typec = metadata["type"]
        if typec == "starcoin":
            profile.set_scoins(profile.get_scoins() + amount)
        elif typec == "grams":
            profile.set_grams(profile.get_grams() + amount)
        else:
            return False
        return True

    @staticmethod
    def award_item(profile, metadata):
        # TODO spawn an item
        pass

    @staticmethod
    def award_experience(profile, metadata):
        amount = metadata["amount"]
        profile.set_experience(profile.get_experience() + amount)
        return True

    @staticmethod
    def award_marque(profile, metadata):
        amount = metadata["amount"]
        profile.distribute_marques(amount)
        return True

    @staticmethod
    def award_page(profile, metadata):
        page_code = metadata["page"]
        typep = metadata["type"]
        if typep == "game":
            profile.set_game_pages(profile.get_game_pages() + page_code)
        elif typep == "carousel":
            profile.set_carousel_pages(profile.get_carousel_pages() + page_code)
        else:
            return False
        return True

    @staticmethod
    def award_accessory(profile, metadata):
        #TODO handle this
        pass

    @staticmethod
    def award_theme(profile, metadata):
        #TODO handle this
        pass

    @staticmethod
    def award_iiq(profile, metadata):
        amount = metadata["amount"]
        profile.set_iiq(profile.get_iiq() + amount)
        if (profile.get_iiq() + amount) > 5000 or (profile.get_iiq() + amount) < 0:
            return False
        return True

    @staticmethod
    def award_rank(profile, metadata):
        to_rank = metadata["new_rank"]
        profile.set_rank(to_rank)
        return True


# Class to hold data about the "type" of item at play. Base information
class ItemTemplate:

    def __init__(self):
        # Default values
        self.name = ""  # Name of this template, for easy reference
        self.max_items = 1  # Max number of items that can be held in this type of itemstack
        self.consume_on_use = 1  # Should items be consumed on use
        self.usable = 1  # Is this item "usable", or is it merely a token
        self.expires = -1  # If anything other than -1, the item will expire after that time - from spawn (denoted in ms)
        self.expire_from = "spawn"  # Can be 'spawn', 'use'
        self.on_use = {}  # Key is a function to be called on use. Value is a dict of metadata to be provided to the method
        self.sort_priority = -1  # If not -1, the highest int item will be displayed first.
        self.rarity = 0
        self.discardable = 0
        self.image = ""

    def to_json(self):
        json_return = {
            "name": self.name,
            "max_items": self.max_items,
            "consume": self.consume_on_use,
            "usable": self.usable,
            "on_use": self.on_use,
            "expire_time_start": self.expire_from,
            "expire_time": self.expires,
            "sort_priority": self.sort_priority,
            "rarity": self.rarity,
            "discardable": self.discardable,
            "image": self.image
        }
        return json_return

    def from_json(self, json_array):
        self.name = json_array['name']
        self.max_items = json_array['max_items']
        self.consume_on_use = json_array['consume']
        self.usable = json_array['usable']
        self.on_use = json_array['on_use']
        self.expire_from = json_array['expire_time_start']
        self.expires = json_array['expire_time']
        self.sort_priority = json_array['sort_priority']
        self.rarity = json_array['rarity']
        self.discardable = json_array['discardable']
        self.image = json_array['image']


# Actual ItemStack object
# Metadata contains fields like:
#   - Original Crafter <for crafted items>
#   - Usage Count <for those types of items>
#   - Previous Owners <for legacy items>
class ItemStack:

    def __init__(self):
        self.template = None  # Holds ItemTemplate, which dictates functionality
        self.amount = 1  # Number of items in this itemstack
        self.metadata = {}  # Internal dictionary to hold string key, object values for things like, who crafted an item/etc...
        self.is_destroyed = False  # Simple variable to hold whether or not this itemstack is destroyed.
            # When the inventory service iterates over a player's inventory, it will ignore and remove ones that are.
        pass

    def from_json(self, json_dict):
        self.template = ItemTemplate()
        self.template.from_json(json_dict['template'])
        self.amount = json_dict['amount']
        self.metadata = json_dict['metadata']

    def to_clean_json(self):
        json_return = {
            "amount": self.amount,
            "metadata": self.metadata,
            "name": self.template.name,
            "max_items": self.template.max_items,
            "consume": self.template.consume_on_use,
            "usable": self.template.usable,
            "on_use": self.template.on_use,
            "expire_time_start": self.template.expire_from,
            "expire_time": self.template.expires,
            "sort_priority": self.template.sort_priority,
            "rarity": self.template.rarity,
            "discardable": self.template.discardable,
            "image": self.template.image
        }
        return json_return

    def to_json(self):
        json_return = {
            "template": self.template.to_json(),
            "amount": self.amount,
            "metadata": self.metadata
        }
        return json_return

    # Method to compare two itemstacks for sorting purposes. Logic goes as follows:
    #   - First, sort_priority is evaluated.
    #       If both are -1, continue to 2)
    #       If one not negative 1, return either 1 (if it's that one) or -1 (if it's this one)
    #       If both not negative 1, continue to 2)
    #   - Second, evaluate name of this item
    #       Lexicographically compare the two
    #   - If they are still equal, (this is literally the same itemstack, but perhaps the first stack was full - very possible,
    #       Compare item amounts. Higher item amount should go first.
    def compare(self, other_itemstack):
        # Phase one
        if self.template.sort_priority != -1:
            if other_itemstack.template.sort_priority != -1:
                # Both are not equal to negative one
                pass
            else:
                # This one is not negative one, that one is.
                # This one goes first.
                return -1
        else:
            if other_itemstack.template.sort_priority != -1:
                # This one is neg, that one isn't
                return 1
            else:
                # This one is neg, that one also is
                pass

        # Phase two
        if self.template.name != other_itemstack.template.name:
            if self.template.name > other_itemstack.template.name:
                # This name is "greater" (occurs ascii later) than the other.
                return 1
            else:
                # Less than/earlier
                return -1

        # Phase three
        if self.amount != other_itemstack.amount:
            if self.amount < other_itemstack.amount:
                return 1
            else:
                return -1

        # They also have the same amount. Default to this one goes after that one.
        return 1

    # Destroy this itemstack
    def destroy(self):
        self.is_destroyed = True

    # Modify the amount of this stack by change.
    def mod_amount(self, change):
        self.amount += change

        if self.amount > self.template.max_items:
            # Too many items!
            self.amount -= change
            return False

        if self.amount <= 0:
            # There are no more items in this stack. Destroy it.
            self.destroy()
            return True

        return True

    # Is this itemstack capable of holding that itemstack?
    def can_hold(self, itemstack):
        if self.template.name == itemstack.template.name:
            # Well, at least it's the same item type. Can it fit?
            current_amount = self.amount
            if (current_amount + itemstack.amount) > self.template.max_items:
                # Adding this one would be too many items in a stack
                return False
            return True
        else:
            return False

    # Method to actually use this item. Returns true if possible/successful, false if not
    def use_item(self, profile):
        for key, value in self.template.on_use.iteritems():
            method_to_call = getattr(ItemUses, key)
            result = method_to_call(profile, self.template.on_use[key])
            if not result:
                return False

        if self.template.consume_on_use:
            self.amount -= 1
            if self.amount <= 0:
                self.destroy()

        return True


# Each inventory is stored individually in a file for the player that should be loaded from json
# when the player logs in.
class Inventory:

    def __init__(self):
        self.items = []  # Array of items within this inventory
        self.size = -1  # How many itemstacks can this inventory hold? Might be upgradeable by backpacks or something
        self.sorted = False

    # Modify this inventory's size by change
    def mod_size(self, change):
        self.size += change

    def get_item(self, slot):
        return self.items[slot]

    # Two questions we need to ask here:
    #   Is there room left in the inventory?
    #   Do we have a previous item in the inventory that can hold this item?
    def add_item(self, itemstack):
        for item in self.items:
            if item.can_hold(itemstack):
                # Hey! We found a place, so let's modify its amount up by this stack's amount
                item.mod_amount(itemstack.amount)
                self.sorted = False  # We are no longer sorted
                return True

        # If we got here, there wasn't a previous item
        if len(self.items) == self.size:
            # The inventory is full. We can't put it in.
            return False
        else:
            # We actually have a spot!
            self.items.append(itemstack)
            self.sorted = False  # We are no longer sorted
            return True

        return False

    def to_clean_json(self):
        dict = {}
        index = 0
        for x in self.items:
            if x:
                dict[str(index)] = x.to_clean_json()
                index+=1

        return_json = {
            "items": dict,
            "size": self.size
        }
        return return_json

    def to_json(self):
        dict = {}
        index = 0
        for x in self.items:
            if x:
                dict[str(index)] = x.to_json()
                index+=1

        return_json = {
            "items": dict,
            "size": self.size
        }
        return return_json

    def from_json(self, json_dict):
        for key, value in json_dict['items'].iteritems():
            stack = ItemStack()
            stack.from_json(value)
            self.items.append(stack)
        self.size = json_dict['size']

    def bubble_sort(self):
        copy_items = self.items[:]
        for passnum in range(len(self.items) -1,0,-1):
            for i in range(passnum):
                this_item = copy_items[i]
                next_item = copy_items[i+1]
                if this_item.compare(next_item) > 0:
                    # This item needs to go next
                    temp = copy_items[i]
                    copy_items[i] = copy_items[i + 1]
                    copy_items[i + 1] = temp

        self.items = copy_items  # Set items to the sorted list, for ease of use
        self.sorted = True  # Mark this inventory as sorted
        return copy_items

    def use_item(self, int_spot):
        if not self.sorted:
            self.sort_items()

        result = self.items[int_spot].use_item()

        if self.items[int_spot].is_destroyed:
            # Remove this spot
            del self.items[int_spot]

        return result

