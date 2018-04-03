import time, os, json
import unicodedata as unc
from Logger import Logger
from ItemCore import Inventory, ItemStack, ItemTemplate, DefaultTemplates


class InventoryService:

    def __init__(self, isogram_server):
        self.isogram_server = isogram_server
        self.file_path = self.isogram_server.get_server_configuration().file_base + "inventories/"

        self.active_inventories = {}  # Dictionary of PID -> Inventory object

        # if os.path.isfile(self.file_path):
        #     self.load()
        # else:
        #     # Create a new one
        #     Logger.log("Creating a new inventory database")
        #     open(self.file_path, "w+")  # Create the new file
        #     self.save()

    def unit_test(self):
        self.load_into_active("1", self.file_path + "Joltned.inv")

        print("\n")
        print(self.get_inventory("1"))
        exit(0)

    # Method to activate a player's inventory object
    def mark_active(self, pid):
        print("Loading inventory for pid " + pid)
        if os.path.isfile(self.file_path + self.isogram_server.get_pid_service().get_profile_from_key(pid).get_account_name() + ".inv"):
            self.load_into_active(pid, self.file_path + self.isogram_server.get_pid_service().get_profile_from_key(pid).get_account_name() + ".inv")
        else:
            # This inventory does not exist. <-- player's first time inventorying
            self.create_new_inventory(self.file_path + self.isogram_server.get_pid_service().get_profile_from_key(pid).get_account_name() + ".inv")
            self.load_into_active(pid, self.file_path + self.isogram_server.get_pid_service().get_profile_from_key(pid).get_account_name() + ".inv")

    def create_new_inventory(self, filepath):
        inv = Inventory()
        inv.size = 25

        welcome_item = ItemStack()
        welcome_item.template = DefaultTemplates.get_lucky_tiki()
        inv.add_item(welcome_item)
        inv.bubble_sort()

        json_inv = inv.to_json()
        with open(filepath, 'w+') as data_file:
            json.dump(json_inv, data_file, ensure_ascii=False)

    def recursive_clean(self, json_dict):
        new_json = {}

        for key, value in json_dict.iteritems():
            if isinstance(value, dict):
                new_json["".join(unc.normalize('NFKD', key).encode('ascii','ignore'))] = self.recursive_clean(value)
            else:
                if isinstance(value, str) or isinstance(value, unicode):
                    new_json["".join(unc.normalize('NFKD', key).encode('ascii','ignore'))] = "".join(unc.normalize('NFKD', value).encode('ascii', 'ignore'))
                else:
                    new_json["".join(unc.normalize('NFKD', key).encode('ascii','ignore'))] = value

        return new_json

    def load_into_active(self, pid, filepath):
        new_json = {}
        with open(filepath) as data_file:
            json_text = json.load(data_file)
            new_json = self.recursive_clean(json_text)

        inv = Inventory()

        inv.from_json(new_json)

        self.active_inventories[pid] = inv

    # Called any time an item is used and the inventory switches around
    def save_inventory(self, pid):
        inv = self.active_inventories[pid]
        json = inv.to_json()
        with open(self.file_path + self.isogram_server.get_pid_service().get_profile_from_key(pid).get_account_name() + ".inv", 'w+') as data_file:
            json.dump(json, self.file_path + self.isogram_server.get_pid_service().get_profile_from_key(pid).get_account_name() + ".inv")

    def use_item(self, pid, slot):
        inv = self.active_inventories[pid]
        result = inv.use_item(slot)
        inv.bubble_sort()
        return result

    def tick(self, tick_count):
        # Are there items that "need" to tick? Can I think of a use case?
        pass

    def get_inventory(self, pid):
        return self.active_inventories[pid]



