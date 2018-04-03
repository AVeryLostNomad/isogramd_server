import time


class MarqueService:

    def __init__(self, isogram_server):
        self.isogram_server = isogram_server
        pass

    def tick(self, tick_count):
        if tick_count % 25 == 0:
            # We only want to do this particular stuff once every twenty five ticks (since a tick is arbitrarily
            #  defined as 30 seconds, this is 12.5 minutes
            for profile in self.isogram_server.get_account_service().get_all_profiles():
                new_pending = {}
                for key, value in profile.get_pending_marques().items():
                    # key was the time set by the distribution
                    # value was the number to increment it by
                    time_now = time.time()
                    if (time_now - key) > (24 * 60 * 60):
                        # It has been more than 24 hours
                        profile.set_marques(profile.get_marques() + value)
                    else:
                        new_pending[key] = value
                profile.set_pending_marques(new_pending)
            self.isogram_server.get_account_service().save()