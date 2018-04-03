import time, threading


class ActivityService():

    def __init__(self, isogram_server):
        self.should_tick = False
        self.isogram_server = isogram_server
        self.waiting_profiles = {}  # Dictionary of profile_email: time_added.
        self.checked_recently = {}  # List of profiles that have been checked "recently". Same form as above
                                    # Accounts are only to be checked once every 10 minutes
        # Accounts have 30 seconds to read the activity check message and verify online presence.
        self.check_inactivity()

    def tick(self, tick_count):
        if not self.should_tick:
            return
        if (tick_count % 2) == 0:
            # Every other tick, sounds about right.
            for profile in self.isogram_server.get_account_service().get_online_profiles():
                if profile.get_email() in self.waiting_profiles.keys() or profile.get_email()\
                        in self.checked_recently.keys():
                    continue
                profile.add_server_message("[ACTIVITY_CHECK]")
                self.waiting_profiles[profile.get_email()] = time.time()
                print("Waiting for activity confirmation from user", profile.get_email())

    def resolve(self, email=None, pid=None):
        if email:
            self.waiting_profiles.pop(email, None)
            self.isogram_server.get_account_service().update_last_activity(email)
            self.checked_recently[email] = time.time()
        if pid:
            profile = self.isogram_server.get_pid_service().get_profile_from_key(pid)
            self.waiting_profiles.pop(profile.get_email())
            self.isogram_server.get_account_service().update_last_activity(profile.get_email())
            self.checked_recently[profile.get_email()] = time.time()

    def check_inactivity(self):
        for key in self.waiting_profiles.keys():
            # Each key is an email
            that_time = self.waiting_profiles[key]
            now_time = time.time()

            difference = now_time - that_time

            if difference > 30:
                self.isogram_server.get_account_service().logout(key)

        to_pop = []
        for key in self.checked_recently:
            that_time = self.checked_recently[key]
            now_time = time.time()

            difference = now_time - that_time

            if difference > (.5 * 60):
                to_pop.append(key)
                # remove this person from checked-recently. They will be checked for inactivity again.
        for key in to_pop:
            self.checked_recently.pop(key, None)

        threading.Timer(15, self.check_inactivity).start()
