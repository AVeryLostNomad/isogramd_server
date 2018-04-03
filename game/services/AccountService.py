import os.path, json, time
from Logger import Logger
from Profile import Profile


class AccountService:

    def __init__(self, isogram_server):
        self.profiles = []  # Should be filled with data from the json
        self.online_profiles = []  # Should be blank every time.
        self.isogram_server = isogram_server
        self.file_path = self.isogram_server.get_server_configuration().file_base + "profiles.json"

        if os.path.isfile(self.file_path):
            self.load()
        else:
            # Create a new one
            Logger.log("Creating a new profile database")
            open(self.file_path, "w+")  # Create the new file
            self.save()
            # We've created the file at this point, we're good to wait until something happens...

    # Method called every server tick.
    def tick(self, tick_count):
        if tick_count % 10 == 0:
            # We only want to do this particular stuff once every ten ticks (since a tick is arbitrarily defined as 30 seconds, this is 300 seconds or 5 minutes
            pindex = 0
            for profile in self.online_profiles[:]:
                if (time.time() - profile.last_active) > 600:
                    # Mark inactive by pulling out of the active list
                    self.online_profiles.pop(pindex)
                pindex += 1

    # Standard functionality for serialization #
    def to_json(self):
        return_json = {
            "profiles": [x.to_json() for x in self.profiles]
        }
        return return_json

    def from_json(self, json_text):
        self.profiles = []
        for item in json_text["profiles"]:
            # These are each profile jsons
            temp_profile = Profile()
            temp_profile.from_json(item)
            self.profiles.append(temp_profile)

    def load(self):
        with open(self.file_path) as data_file:
            json_text = json.load(data_file)
        self.from_json(json_text)

    def save(self):
        with open(self.file_path, 'w') as data_file:
            json.dump(self.to_json(), data_file)
    # ---------------------------------------- #

    # Functions to create / interact with accounts

    def register(self, email, password, context={}):
        if self.profile_exists(email=email):
            return False
        new_profile = Profile()  # Initializes everything to default
        new_profile.set_email(email)
        new_profile.set_password(password)
        # TODO send the email for registration and such
        # TODO the email that verifies this account will be the "main" IP address
        random_id = self.isogram_server.get_verification_service().add_pending(email, context)
        self.profiles.append(new_profile)  # Add it in
        self.save()
        return random_id

    def get_profile_from_email(self, email):
        for profile in self.profiles:
            if profile.get_email() == email:
                # This is the profile
                return profile
        return None

    def get_profile_from_username(self, username):
        for profile in self.profiles:
            if profile.get_account_name() == username:
                # This is the profile
                return profile
        return None

    def profile_exists(self, email="", username=""):
        for profile in self.profiles:
            if profile.get_email() == email:
                return True
            if profile.get_account_name() == username and profile.get_account_name() != "":
                return True
        return False

    def username_exists(self, username):
        for profile in self.profiles:
            if profile.get_account_name() == username:
                return True
        return False

    def profile_verified(self, email="", username=""):
        for profile in self.profiles:
            if profile.get_email() == email:
                return profile.get_verified()
            if profile.get_account_name() == username:
                return profile.get_verified()
        return False

    def verify(self, email, context={}):
        profile = self.get_profile_from_email(email)
        profile.set_verified(True)
        trusted_ips = profile.get_trusted_ips()
        trusted_ips[context["device_name"]] = context["ip"]
        profile.set_trusted_ips(trusted_ips)
        self.save()

    def correct_pass(self, email, password):
        correct_details = False
        the_profile = None
        for profile in self.profiles:
            if profile.get_email() == email:
                if profile.get_password() == password:
                    correct_details = True
            the_profile = profile
        if not correct_details:
            return False
        return True

    def trusted_context(self, email, context={}):
        the_profile = self.get_profile_from_email(email)
        if context["ip"] in the_profile.get_trusted_ips().values():
            return True
        else:
            return False

    def login(self, email, password, context={}):
        if not self.profile_exists(email):
            return False, ""
        # The profile does exist, but is this it's password?
        correct_details = False
        the_profile = None
        for profile in self.profiles:
            if profile.get_email() == email:
                # This is the profile
                if profile.get_password() == password:
                    # This is the account. Woot woot, maybe?
                    correct_details = True
                    the_profile = profile
        if not correct_details:
            # Wasn't correct password
            return False, ""
        if not self.profile_verified(email=email):
            # Profile has not yet been verified
            return False, ""
        # Before we give this person the all-clear, let's go ahead and check IP address for validity
        if context["ip"] in the_profile.get_trusted_ips().values():
            # This is a trusted IP address. We're all clear
            if the_profile in self.online_profiles:
                self.isogram_server.get_pid_service().terminate_pid_association_profile(the_profile)
            if the_profile not in self.online_profiles:
                self.online_profiles.append(the_profile)
            return True, self.isogram_server.get_pid_service().register_profile(the_profile)
        else:
            # TODO send an email/text indicating that there was a login from an untrusted location and to reply/do
            # TODO something if "that was me"
            return False, ""

    # Functions on the accounts #

    def update_last_activity(self, email):
        profile = self.get_profile_from_email(email)
        profile.set_last_active(time.time())
        self.save()

    def get_all_profiles(self):
        return self.profiles

    def logout(self, email):
        profile = self.get_profile_from_email(email)
        index = 0
        for prof in self.online_profiles:
            if prof.get_email() == profile.get_email():
                self.online_profiles.pop(index)
                break
            index+=1
        self.isogram_server.get_pid_service().terminate_pid_association_profile(profile)
        # Log em out!

        for match in self.isogram_server.get_match_service().get_matches():
            if match.is_player_involved(profile):
                # We need to remove this game, if (and only if, presumably) it is a single game
                if match.get_desired_number_of_players() == 1:
                    self.isogram_server.get_match_service().pop_game(match.id, do_record=False)
                else:
                    # TODO figure out how to handle games that have more than one player if one of them quits.
                    pass

    def get_online_profiles(self):
        return self.online_profiles

    def get_online_profiles_json(self):
        return [profile.to_json(hide_personal_details=True) for profile in self.online_profiles]


