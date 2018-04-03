import json
from Theme import Theme
from Avatar import Avatar
import time
import UsernameGenerator


class Profile:

    def __init__(self):
        self.personal_detail_fields = ["real_name", "address", "email", "password", "trusted_ips", "phone_number",
                                       "verified", "pending_messages"]
        self.stats_fields = ["win_streak", "loss_streak", "wins_total", "losses_total", "largest_loss_streak",
                             "largest_win_streak", "perfect_victory", "total_play_time_by_size", "total_moves_by_size",
                             "total_games_by_size", "iiq", "win_loss_ratio"]

        # Identification Information
        self.real_name = ""  # Name of the person associated with this account
        self.address = ""
        self.email = ""
        self.password = ""
        self.trusted_ips = {}
        self.phone_number = ""

        self.pending_messages = {}  # Dictionary containing message ID: message, timestamp
        self.postgame_messages = {}

        self.verified = False

        # Account information
        self.name = UsernameGenerator.generate_isogramic_username()  # Username of the user
        self.catchphrase = ""  # Phrase to show to those starting a game with you.

        # Cosmetic information
        self.theme = Theme()  # Theme the user has equipped
        self.avatar = Avatar()  # Link to avatar object, built from json, of course.

        # Play-stats
        self.last_active = 0
        self.win_streak = 0
        self.loss_streak = 0
        self.wins_total = 0
        self.losses_total = 0
        self.largest_win_streak = 0
        self.largest_loss_streak = 0
        self.perfect_victory = 0
        self.total_play_time_by_size = Profile.by_size(3, 17)
        self.total_moves_by_size = Profile.by_size(3, 17)
        self.total_games_by_size = Profile.by_size(3, 17)

        # Important Stats
        self.iiq = 2500  # Isogram Intelligence Quotient
        self.win_loss_ratio = 0

        self.level = 0  # Level
        self.experience = 0  # Total experience
        self.carousel_pages = "P"  # Order of pages on this player's carousel.
        self.game_pages = "LG"  # Order of pages on this player's game carousel, visible during matches.

        self.grams = 0  # Grams of stardust
        self.scoins = 0  # Star coins
        self.marques = 0  # "Sorry" tickets. Distributed to players upon unfortunate circumstances or at admin discretion.
                          # Redeemable 24 hours after distribution.
        self.pending_marques = {}

        self.rank = 0  # Default rank. 0 - Normal, 1 - Community Helper, 2 - Moderator, 3 - Admin

    def to_json(self, hide_personal_details=False, just_stats=False):
        return_json = {
            'verified': self.verified,
            'last_active': self.last_active,
            'real_name': self.real_name,
            'phone_number': self.phone_number,
            'address': self.address,
            'email': self.email,
            'name': self.name,
            'catchphrase': self.catchphrase,
            'theme': self.theme.to_json(),
            'avatar': self.avatar.to_json(),
            'win_streak': self.win_streak,
            'loss_streak': self.loss_streak,
            'wins_total': self.wins_total,
            'losses_total': self.losses_total,
            'largest_loss_streak': self.largest_loss_streak,
            'largest_win_streak': self.largest_win_streak,
            'perfect_victory': self.perfect_victory,
            'total_play_time_by_size': self.total_play_time_by_size,
            'total_moves_by_size': self.total_moves_by_size,
            'total_games_by_size': self.total_games_by_size,
            'iiq': self.iiq,
            'win_loss_ratio': self.win_loss_ratio,
            'password': self.password,
            'trusted_ips': self.trusted_ips,
            'level': self.level,
            'carousel_pages': self.carousel_pages,
            'game_pages': self.game_pages,
            'grams': self.grams,
            'scoins': self.scoins,
            'marques': self.marques,
            'pending_marques': self.pending_marques,
            'experience': self.experience,
            'rank': self.rank
        }
        if hide_personal_details:
            for entry in self.personal_detail_fields:
                return_json.pop(entry, None)
        if just_stats:
            for entry in return_json.keys():
                if entry not in self.stats_fields:
                    return_json.pop(entry, None)

        return return_json

    @staticmethod
    def by_size(start, end):
        return_dict = {}
        for x in xrange(start, end+1):
            return_dict[x] = 0
        return return_dict

    def from_json(self, json_text):
        self.real_name = json_text["real_name"]
        self.address = json_text["address"]
        self.email = json_text["email"]
        self.name = json_text["name"]
        self.catchphrase = json_text["catchphrase"]
        temp_theme = Theme()
        temp_theme.from_json(json_text["theme"])
        self.theme = temp_theme
        temp_avatar = Avatar()
        temp_avatar.from_json(json_text["avatar"])
        self.avatar = temp_avatar
        self.win_streak = json_text["win_streak"]
        self.loss_streak = json_text["loss_streak"]
        self.wins_total = json_text["wins_total"]
        self.losses_total = json_text["losses_total"]
        self.perfect_victory = json_text["perfect_victory"]
        self.total_play_time_by_size = json_text["total_play_time_by_size"]
        self.total_moves_by_size = json_text["total_moves_by_size"]
        self.total_games_by_size = json_text["total_games_by_size"]
        self.largest_loss_streak = json_text["largest_loss_streak"]
        self.largest_win_streak = json_text["largest_win_streak"]
        self.iiq = json_text["iiq"]
        self.win_loss_ratio = json_text["win_loss_ratio"]
        self.password = json_text["password"]
        self.trusted_ips = json_text["trusted_ips"]
        self.phone_number = json_text["phone_number"]
        self.last_active = json_text["last_active"]
        self.verified = json_text["verified"]
        self.level = json_text["level"]
        self.carousel_pages = json_text["carousel_pages"]
        self.game_pages = json_text["game_pages"]
        self.scoins = json_text["scoins"]
        self.grams = json_text["grams"]
        self.marques = json_text["marques"]
        self.pending_marques = json_text["pending_marques"]
        self.experience = json_text["experience"]
        self.rank = json_text["rank"]

    def set_real_name(self, newname):
        self.real_name = newname

    def get_real_name(self):
        return self.real_name

    def set_address(self, naddress):
        self.address = naddress

    def get_address(self):
        return self.address

    def set_email(self, nemail):
        self.email = nemail

    def get_email(self):
        return self.email

    def set_account_name(self, naname):
        self.name = naname

    def get_account_name(self):
        return self.name

    def set_catchphrase(self, ncatchphrase):
        self.catchphrase = ncatchphrase

    def get_catchphrase(self):
        return self.catchphrase

    def set_theme(self, ntheme):
        self.theme = ntheme

    def get_theme(self):
        return self.theme

    def set_avatar(self, navatar):
        self.avatar = navatar

    def get_avatar(self):
        return self.avatar

    def set_win_streak(self, nwin):
        self.win_streak = nwin

    def get_win_streak(self):
        return self.win_streak

    def set_loss_streak(self, nloss):
        self.loss_streak = nloss

    def get_loss_streak(self):
        return self.loss_streak

    def set_wins_total(self, nwins):
        self.wins_total = nwins

    def get_wins_total(self):
        return self.wins_total

    def set_losses_total(self, nlosses):
        self.losses_total = nlosses

    def get_losses_total(self):
        return self.losses_total

    def set_perfect_victories(self, npvict):
        self.perfect_victory = npvict

    def get_perfect_victories(self):
        return self.perfect_victory

    def set_iiq(self, niiq):
        self.iiq = niiq

    def get_iiq(self):
        return self.iiq

    def set_win_loss_ratio(self, nwlr):
        self.win_loss_ratio = nwlr

    def get_win_loss_ratio(self):
        return self.win_loss_ratio

    def get_total_play_time_by_size(self):
        return self.total_play_time_by_size

    def set_total_play_time_by_size(self, dict):
        self.total_play_time_by_size = dict

    def get_total_games_by_size(self):
        return self.total_games_by_size

    def set_total_games_by_size(self, dict):
        self.total_games_by_size = dict

    def set_total_moves_by_size(self, dict):
        self.total_moves_by_size = dict

    def get_total_moves_by_size(self):
        return self.total_moves_by_size

    def set_password(self, passw):
        self.password = passw

    def get_password(self):
        return self.password

    def get_trusted_ips(self):
        return self.trusted_ips

    def set_trusted_ips(self, tips):
        self.trusted_ips = tips

    def get_phone_number(self):
        return self.phone_number

    def set_phone_number(self, phone):
        self.phone_number = phone

    def set_last_active(self, time):
        self.last_active = time

    def get_last_active(self):
        return self.last_active

    def get_verified(self):
        return self.verified

    def set_verified(self, bool):
        self.verified = bool

    def get_pending_messages(self):
        return self.pending_messages

    def get_postgame_messages(self):
        return self.postgame_messages

    def set_largest_loss_streak(self, nll):
        self.largest_loss_streak = nll

    def get_largest_loss_streak(self):
        return self.largest_loss_streak

    def set_largest_win_streak(self, nww):
        self.largest_win_streak = nww

    def get_largest_win_streak(self):
        return self.largest_win_streak

    def clear_pending_messages(self):
        self.pending_messages.clear()

    def add_server_message(self, string_message, is_json=False):
        largest_key = 0
        for key in self.pending_messages.keys():
            if key > largest_key:
                largest_key = key
        self.pending_messages[largest_key + 1] = {
            "message": string_message,
            "timestamp": time.time(),
            "is_json": is_json
        }

    def clear_postgame_messages(self):
        self.postgame_messages.clear()

    def add_postgame_message(self, string_message, is_json=False):
        largest_key = 0
        for key in self.postgame_messages.keys():
            if key > largest_key:
                largest_key = key
        self.postgame_messages[largest_key + 1] = {
            "message": string_message,
            "timestamp": time.time(),
            "is_json": is_json
        }

    def get_level(self):
        return self.level

    def set_level(self, level):
        self.level = level

    def get_carousel_pages(self):
        return self.carousel_pages

    def set_carousel_pages(self, target):
        self.carousel_pages = target

    def get_game_pages(self):
        return self.game_pages

    def set_game_pages(self, target):
        self.game_pages = target

    def set_scoins(self, scoins):
        self.scoins = scoins

    def get_scoins(self):
        return self.scoins

    def set_grams(self, gram):
        self.grams = gram

    def get_grams(self):
        return self.grams

    def get_marques(self):
        return self.marques

    def set_marques(self, newmarques):
        self.marques = newmarques

    def get_pending_marques(self):
        return self.pending_marques

    def set_pending_marques(self, newpend):
        self.pending_marques = newpend

    def distribute_marques(self, amount=1):
        self.pending_marques[time.time()] = amount

    def get_experience(self):
        return self.experience

    def set_experience(self, amount):
        self.experience = amount

    def get_rank(self):
        return self.rank

    def set_rank(self, newrank):
        self.rank = newrank
