import json, os, random, string, time
from Logger import Logger


class VerificationService:

    def __init__(self, isogram_server):
        self.pending_verifies = []  # List of dictionaries
        self.isogram_server = isogram_server
        self.file_path = self.isogram_server.get_server_configuration().file_base + "verification.json"

        if os.path.isfile(self.file_path):
            self.load()
        else:
            # Create a new one
            Logger.log("Creating a new verification database")
            open(self.file_path, "w+")  # Create the new file
            self.save()

    # Makes pending verifications automatically expire after 24 hours
    def tick(self, tick_count):
        if tick_count % 50 == 0:
            # We only want to do this particular stuff once every fifty ticks (since a tick is arbitrarily
            #  defined as 30 seconds, this is 25 minutes
            pindex = 0
            for entry in self.pending_verifies[:]:
                time_now = time.time()
                if (time_now - entry["created_at"]) > 86400:
                    self.pending_verifies.pop(pindex)
                pindex += 1
            self.save()

    def to_json(self):
        return_json = {
            "pending": self.pending_verifies
        }
        return return_json

    def from_json(self, json_text):
        self.pending_verifies = json_text["pending"]

    def load(self):
        with open(self.file_path) as data_file:
            json_text = json.load(data_file)
        self.from_json(json_text)

    def save(self):
        with open(self.file_path, 'w') as data_file:
            json.dump(self.to_json(), data_file)

    def is_valid_id(self, random_id):
        for entry in self.pending_verifies:
            if entry["id"] == random_id:
                # We found one
                return True
        return False

    def is_proper_device(self, random_id, context={}):
        if not self.is_valid_id(random_id):
            return False
        for entry in self.pending_verifies:
            if entry["id"] == random_id:
                #  This is the one. Check our IP
                if entry["ip"] == context["ip"]:
                    return True
                else:
                    # Bad bad, proper everything but wrong device. Fix 'er up
                    self.pending_verifies.remove(entry)
                    self.save()
        return False

    def remove_prepending(self, email):
        for entry in self.pending_verifies:
            if entry["email"] == email:
                self.pending_verifies.remove(entry)
                self.save()
                return True
        return False

    # Returns randomly generated ID string
    def add_pending(self, email, context={}):
        random_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(25))
        entry = {
            "ip": context["ip"],
            "device_name": context["device_name"],
            "email": email,
            "id": random_id,
            "created_at": time.time()
        }
        self.pending_verifies.append(entry)
        self.save()
        return random_id

    def resolve(self, random_id, context={}):
        for entry in self.pending_verifies:
            if entry["id"] == random_id:
                #  This is the one. Check our IP
                if entry["ip"] == context["ip"]:
                    # Solid! We can verify successfully
                    self.isogram_server.get_account_service().verify(entry["email"], context)
                    self.pending_verifies.remove(entry)
                    self.save()
                    return True
        return False




