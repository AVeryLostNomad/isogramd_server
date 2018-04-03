import json
import random
import threading
import time

from flask import Flask, request

from AccountService import AccountService
from AverageStatsService import AverageStatsService
from BaseGame import Move
from MatchService import MatchService
from PIDService import PIDService
from ServerConfiguration import ServerConfiguration
from VerificationService import VerificationService
from MarqueService import MarqueService
from RewardService import RewardService
from ActivityService import ActivityService
from Words import Words
from Email import send_mail
from InventoryService import InventoryService

app = Flask(__name__)
english_word_db = Words(do_print_debug=False)

version_string = "0.0.01"

print("Isogram Server v" + version_string)

SKIP_VERIFY = True

class Server:

    def __init__(self, word_db):
        self.server_configuration = ServerConfiguration(self)
        self.inventory_service = InventoryService(self)
        self.stat_service = AverageStatsService(self)
        self.match_service = MatchService(self)
        self.verification_service = VerificationService(self)
        self.account_service = AccountService(self)
        self.pid_service = PIDService(self)
        self.activity_service = ActivityService(self)
        self.marque_service = MarqueService(self)
        self.reward_service = RewardService(self)
        self.word_db = word_db

    def get_server_configuration(self):
        return self.server_configuration

    def get_account_service(self):
        return self.account_service

    def get_verification_service(self):
        return self.verification_service

    def get_marque_service(self):
        return self.marque_service

    def get_match_service(self):
        return self.match_service

    def get_pid_service(self):
        return self.pid_service

    def get_stat_service(self):
        return self.stat_service

    def get_activity_service(self):
        return self.activity_service

    def get_reward_service(self):
        return self.reward_service

    def get_word_db(self):
        return self.word_db

    def get_inventory_service(self):
        return self.inventory_service

server = Server(english_word_db)

tick_count = 2
def server_tick():
    server.get_match_service().tick(tick_count)
    server.get_account_service().tick(tick_count)
    server.get_verification_service().tick(tick_count)
    server.get_activity_service().tick(tick_count)
    server.get_marque_service().tick(tick_count)
    threading.Timer(30, server_tick).start()

server_tick()  # First and last tick call

def get_context():
    if 'X-Forwarded-For' in request.headers:
        remote_addr = request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1]
    else:
        remote_addr = request.remote_addr or 'untrackable'
    context = {
        "ip": remote_addr,
        "device_name": "TempDeviceName"
    }
    return context

@app.route('/')
def hello_world():
    return json.dumps({"result": "okay", "action": "handshake"})

@app.route("/list_online")
def list_online():
    return json.dumps({"result": "okay", "action": "list_online","payload":{
        "list": server.get_account_service().get_online_profiles_json(),
        "count": len(server.get_account_service().get_online_profiles_json())
    }})

# Debug functions #

@app.route('/serve_random')
def serve_random():
    args = request.args
    if args.get("size"):
        word = random.choice(english_word_db.iso_dict[int(args.get("size"))])
        return json.dumps({"result": "temporary", "action": "serve_random",
                           "payload": {"chosen_word": word, "length": len(word)}})
    word = random.choice(random.choice(english_word_db.iso_dict.values()))
    return json.dumps({"result": "temporary", "action": "serve_random", "payload": {
        "chosen_word": word,
        "length": len(word)
    }})

@app.route("/queue")
def queue():
    args = request.args
    if args.get("pid"):
        if args.get("for"):
            server.get_match_service().queue_for_match(args.get("pid"), [x.strip() for x in args.get("for").split(',')])
            return json.dumps({
                "result": "okay",
                "action": "queue",
                "payload": {
                    "success": True,
                    "message": "Placed in queue"
                }
            })
        else:
            server.get_match_service().queue_for_match(args.get("pid"), ["practice"])
            return json.dumps({
                "result": "okay",
                "action": "queue",
                "payload":{
                    "success": True,
                    "message": "Placed in queue"
                }
            })
    else:
        return json.dumps({
            "result": "okay",
            "action": "queue",
            "payload":{
                "success": False,
                "message": "Please provide a pid"
            }
        })

@app.route("/get_game_description")
def get_game_desc():
    args = request.args
    if args.get("gameid"):
        match = server.get_match_service().get_game_from_gameid(args.get("gameid"))
        return json.dumps({
            "result": "okay",
            "action": "get_game_desc",
            "payload": {
                "success": True,
                "message": {
                    "name": match.get_name(),
                    "desc": match.get_description()
                }
            }
        })
    else:
        return json.dumps({
            "result": "okay",
            "action": "get_game_desc",
            "payload": {
                "success": False,
                "message": "Missing game-id"
            }
        })


@app.route("/get_opponent_stats")
def get_opponent_stats():
    args = request.args
    if args.get("gameid") and args.get("pid"):
        match = server.get_match_service().get_game_from_gameid(args.get("gameid"))
        this_player_profile = server.get_pid_service().get_profile_from_key(args.get("pid"))
        opponents = match.get_opponents(this_player_profile)
        if len(opponents) == 0:
            return json.dumps({
                "result": "okay",
                "action": "get_opponent_stats",
                "payload": {
                    "success": False,
                    "message": "Yourself"
                }
            })
        dict_of_opponents = {}
        index = 0
        for profil in [prof.to_json(hide_personal_details=True) for prof in opponents]:
            dict_of_opponents[str(index)] = profil
            index = index + 1
        return json.dumps({
            "result": "okay",
            "action": "get_opponent_stats",
            "payload": {
                "success": True,
                "message": dict_of_opponents
            }
        })
    else:
        return json.dumps({
            "result": "okay",
            "action": "get_opponent_stats",
            "payload": {
                "success": False,
                "message": "Missing either pid or game-id"
            }
        })



@app.route("/my_profile_status")
def my_profile_status():
    args = request.args
    if args.get("pid"):
        # They want player status
        profile = server.get_pid_service().get_profile_from_key(args.get("pid"))
        if profile is None:
            print("Return null")
            return json.dumps({
                "result": "okay",
                "action": "status_player",
                "payload":{
                    "success": False,
                    "message": "Invalid player ID"
                }
            })
        response = json.dumps({
            "result": "okay",
            "action": "status_player",
            "payload":{
                "success": True,
                "profile": profile.to_json()
            }
        })
        print("Return " + response)
        return response

@app.route("/guess")
def guess():
    args = request.args
    if args.get("pid") and args.get("guess") and args.get("game"):
        # We can do things with this
        match = server.get_match_service().get_game_from_gameid(args.get("game"))
        if match is None:
            return json.dumps({
                "result": "okay",
                "action": "guess",
                "payload":{
                    "success": False,
                    "message": "Invalid game ID"
                }
            })

        if server.get_pid_service().get_profile_from_key(args.get("pid")) is None:
            return json.dumps({
                "result": "okay",
                "action": "guess",
                "payload": {
                    "success": False,
                    "message": "Invalid player ID, please relog."
                }
            })
        move = {
            "game_id": args.get("game"),
            "guess": args.get("guess"),
            "timestamp": time.time()
        }
        mv = Move()
        mv.from_json(move)
        match.record_move(str(args.get("pid")), mv)
        return json.dumps({
            "result": "okay",
            "action": "guess",
            "payload": {
                "success": True
            }
        })
    else:
        return json.dumps({
            "result": "okay",
            "action": "guess",
            "payload":{
                "success": False,
                "message": "We need a pid, guess, and a game id"
            }
        })

@app.route('/queue_options')
def get_queue_options():
    args = request.args
    if args.get("pid"):
        pid = args.get("pid")
        profile = server.get_pid_service().get_profile_from_key(args.get("pid"))
        strings = []
        for game in server.get_match_service().match_types.keys():
            base_game = server.get_match_service().match_types[game]
            if(base_game.is_suitable_player(pid, get_context())):
                strings.append(game)
        return json.dumps({
            "result": "okay",
            "action": "get_queue_options",
            "payload": {
                "success": True,
                "message": strings
            }
        })

    else:
        return json.dumps({
            "result": "okay",
            "action": "get_queue_options",
            "payload": {
                "success": False,
                "message": "Please provide a pid log in."
            }
        })

@app.route('/clear_all_messages')
def clear_all_messages():
    args = request.args
    if args.get("pid"):
        profile = server.get_pid_service().get_profile_from_key(args.get("pid"))
        if profile is None:
            return json.dumps({
                "result": "okay",
                "action": "clear_all_messages",
                "payload": {
                    "success": False,
                    "message": "Invalid profile-id. Please re-login."
                }
            })
        profile.clear_pending_messages()
        profile.clear_postgame_messages()
        string = json.dumps({
            "result": "okay",
            "action": "clear_all_messages",
            "payload": {
                "success": True
            }
        })
        print(string)
        return string
    else:
        return json.dumps({
            "result": "okay",
            "action": "clear_all_messages",
            "payload": {
                "success": False,
                "message": "Please provide a profile-id via log-in."
            }
        })

@app.route('/get_postgame')
def get_postgame():
    args = request.args
    if args.get("pid"):
        profile = server.get_pid_service().get_profile_from_key(args.get("pid"))
        if profile is None:
            return json.dumps({
                "result": "okay",
                "action": "get_postgame",
                "payload": {
                    "success": False,
                    "message": "Invalid profile-id. Please re-login."
                }
            })
        try:
            messages = profile.get_postgame_messages()
        except:
            return json.dumps({
                "result": "okay",
                "action": "get_postgame",
                "payload": {
                    "success": False,
                    "message": "Invalid profile-id. Please re-login."
                }
            })
        string = json.dumps({
            "result": "okay",
            "action": "get_postgame",
            "payload": {
                "success": True,
                "messages": messages
            }
        })
        print(string)
        return string
    else:
        return json.dumps({
            "result": "okay",
            "action": "get_postgame",
            "payload": {
                "success": False,
                "message": "Please provide a profile-id via log-in."
            }
        })

@app.route('/get_messages')
def get_messages():
    args = request.args
    if args.get("pid"):
        profile = server.get_pid_service().get_profile_from_key(args.get("pid"))
        if profile is None:
            return json.dumps({
                "result": "okay",
                "action": "get_messages",
                "payload": {
                    "success": False,
                    "message": "Invalid profile-id. Please re-login."
                }
            })
        try:
            messages = profile.get_pending_messages()
        except:
            return json.dumps({
                "result": "okay",
                "action": "get_messages",
                "payload": {
                    "success": False,
                    "message": "Invalid profile-id. Please re-login."
                }
            })
        string = json.dumps({
            "result": "okay",
            "action": "get_messages",
            "payload": {
                "success": True,
                "messages": messages
            }
        })
        print(string)
        return string
    else:
        return json.dumps({
            "result": "okay",
            "action": "get_messages",
            "payload": {
                "success": False,
                "message": "Please provide a profile-id via log-in."
            }
        })

@app.route("/player_stats")
def stats():
    args = request.args
    if args.get("email"):
        context = get_context()
        profile = server.get_account_service().get_profile_from_email(args.get("email"))
        if profile is None:
            return json.dumps({
                "result": "okay",
                "action": "stats",
                "payload":{
                    "success": False,
                    "message": "Profile not found."
                }
            })
        return json.dumps({
            "result": "okay",
            "action": "stats",
            "payload":{
                "success": True,
                "message": "Profile found, stats retrieved.",
                "stats": profile.to_json(just_stats=True)
            }
        })
    elif args.get("username"):
        context = get_context()
        profile = server.get_account_service().get_profile_from_username(args.get("username"))
        if profile is None:
            return json.dumps({
                "result": "okay",
                "action": "stats",
                "payload": {
                    "success": False,
                    "message": "Profile not found."
                }
            })
        return json.dumps({
            "result": "okay",
            "action": "stats",
            "payload": {
                "success": True,
                "message": "Profile found, stats retrieved.",
                "stats": profile.to_json(just_stats=True)
            }
        })
    else:
        return json.dumps({
            "result": "okay",
            "action": "stats",
            "payload":{
                "success": False,
                "message": "Please provide an email or username"
            }
        })

@app.route("/login")
def login():
    args = request.args
    if args.get("email") and args.get("password"):
        context = get_context()
        result, pid = server.get_account_service().login(args.get("email"), args.get("password"), context)
        if result:
            # We logged in
            server.get_inventory_service().mark_active(pid)
            server.get_pid_service().get_profile_from_key(pid).clear_pending_messages()
            return json.dumps({
                "result": "okay",
                "action": "login",
                "payload":{
                    "success": True,
                    "message": "Logged in successfully!",
                    "player_id": pid
                }
            })
        else:
            # Nope! What was the isuse?
            if not server.get_account_service().profile_exists(args.get("email")):
                return json.dumps({
                    "result": "okay",
                    "action": "login",
                    "payload":{
                        "success": False,
                        "message": "Account does not exist"
                    }
                })
            if not server.get_account_service().profile_verified(args.get("email")):
                return json.dumps({
                    "result": "okay",
                    "action": "login",
                    "payload":{
                        "success": False,
                        "message": "Account not verified"
                    }
                })
            if not server.get_account_service().correct_pass(args.get("email"), args.get("password")):
                return json.dumps({
                    "result": "okay",
                    "action": "login",
                    "payload":{
                        "success": False,
                        "message": "Wrong user credentials!"
                    }
                })
            if not server.get_account_service().trusted_context(args.get("email"), context):
                return json.dumps({
                    "result": "okay",
                    "action": "login",
                    "payload":{
                        "success": False,
                        "message": "Connecting from untrusted IP address",
                        "recommendation": "Connect to '" + server.get_server_configuration().get_domain() +
                                          "/trust_ip' to add a trusted device"
                    }
                })
            return json.dumps({
                "result": "error",
                "action": "login",
                "payload":{
                    "success": False,
                    "message": "Some unknown error occurred. Please contact admins for assistance"
                }
            })
    else:
        return json.dumps({
            "result": "okay",
            "action": "login",
            "payload":{
                "success": False,
                "message": "Please provide an email and password"
            }
        })

@app.route("/trust_ip")
def trust_ip():
    args = request.args
    if args.get("email") and args.get("device_name"):
        # Offer to do this, if verified
        context = get_context()
        random_id = server.get_verification_service().add_pending(args.get("email"), context)
        return json.dumps({
            "result": "okay",
            "action": "trust_ip",
            "payload": {
                "success": True,
                "message": "Verify at " + server.get_server_configuration().get_domain() + " /verify/" + random_id
            }
        })
    else:
        return json.dumps({
            "result": "okay",
            "action": "register",
            "payload":{
                "success": False,
                "message": "Please provide an email and new device name"
            }
        })

# TODO CHECK ACCOUNT EXISTS
@app.route("/register")
def register():
    args = request.args
    if args.get("email") and args.get("password"):
        # We can do a register
        context = get_context()
        random_id = server.get_account_service().register(args.get("email"), args.get("password"), context)

        link = server.get_server_configuration().get_domain() + "/verify/" + random_id
        if SKIP_VERIFY:
            server.get_verification_service().resolve(random_id, context)
        else:
            send_mail(args.get("email"), link)
        return json.dumps({
            "result": "okay",
            "action": "register",
            "payload": {
                "success": True,
                "message": "Verification link sent to email"
            }
        })
    else:
        return json.dumps({
            "result": "okay",
            "action": "register",
            "payload":{
                "success": False,
                "message": "Please provide an email and password"
            }
        })

@app.route("/resend_verification")
def resend_verification():
    args = request.args
    if args.get("email"):
        context = get_context()
        if not server.get_account_service().profile_exists(args.get("email")):
            # This isn't a registered profile
            return json.dumps({
                "result": "okay",
                "action": "resend_verification",
                "payload":{
                    "success": False,
                    "message": "This email was never registered",
                    "recommendation": "Visit " + server.get_server_configuration().domain + "/register" + " to do so"
                }
            })
        if server.get_account_service().profile_verified(args.get("email")):
            # This profile is already verified
            return json.dumps({
                "result": "okay",
                "action": "resend_verification",
                "payload": {
                    "success": False,
                    "message": "This profile is already verified",
                    "recommendation": "If you want to add a trusted device, do so through your account menu"
                }
            })

        # We are ready to resend verification, I suppose, to this person's email
        # TODO send to the email
        if server.get_verification_service().remove_prepending(args.get("email")):
            # Successfully resent this one.
            random_id = server.get_verification_service().add_pending(args.get("email"), context)
            return json.dumps({
                "result": "okay",
                "action": "register",
                "payload": {
                    "success": True,
                    "message": "Verify at " + server.get_server_configuration().get_domain() + "/verify/" + random_id
                }
            })
        else:
            return json.dumps({
                "result": "okay",
                "action": "resend_verficiation",
                "payload":{
                    "success": False,
                    "message": "Error resending verification email. Contact admins if this issue persists"
                }
            })
    else:
        return json.dumps({
            "result": "okay",
            "action": "resend_verification",
            "payload":{
                "success": False,
                "message": "Please provide the email that you originally verified with"
            }
        })

@app.route("/active")
def still_active():
    args = request.args
    if args.get("pid"):
        print("Got activity confirmation for user ", args.get("pid"))
        server.get_activity_service().resolve(pid=args.get("pid"))
        return json.dumps({
            "result": "okay",
            "action": "register",
            "payload": {
                "success": True,
                "message": "Activity marked"
            }
        })
    elif args.get("email"):
        print("Got activity confirmation for user ", args.get("email"))
        server.get_activity_service().resolve(email=args.get("email"))
        return json.dumps({
            "result": "okay",
            "action": "register",
            "payload": {
                "success": True,
                "message": "Activity marked"
            }
        })
    else:
        return json.dumps({
            "result": "okay",
            "action": "register",
            "payload": {
                "success": False,
                "message": "Please provide an email"
            }
        })

@app.route('/verify/<IDSTRING>', methods=['GET', 'POST'])
def verification_routing(IDSTRING):
    context = get_context()
    if server.get_verification_service().resolve(IDSTRING, context):

        return json.dumps({"result":"okay", "action": "verify_account", "payload":{
            "success": True,
            "message": "You may now log in"
        }})
    else:
        id_bad = server.get_verification_service().is_valid_id(IDSTRING)
        device_bad = server.get_verification_service().is_proper_device(IDSTRING, context)
        if id_bad:
            reason = "Invalid verification string. Perhaps yours has expired?"
            recommendation = "Visit " + server.get_server_configuration().get_domain() + "/resend_verification " \
                                                                                         "to get a new one"
        elif device_bad:
            reason = "Invalid device. Was expecting verification from the same IP you registered on."
            recommendation = "Visit " + server.get_server_configuration().get_domain() + "/resend_verification " \
                                                                                         "to get a verification for" \
                                                                                         "this device."
        else:
            reason = "No idea"
            recommendation = "Sorry!"
        return json.dumps({"result": "okay", "action": "verify_account", "payload": {
            "success": False,
            "message": "Some issue occurred during account verification",
            "reason": reason,
            "recommendation": recommendation
        }})

@app.route("/pregame")
def pregame():
    args = request.args
    if args.get("pid"):
        # They specified pid, which is good, because we only allow players involved in the game to do pregaming.
        if args.get("game"):
            match = server.get_match_service().get_game_from_gameid(args.get("game"))
            if match is None:
                return json.dumps({
                    "result": "okay",
                    "action": "pregame_info",
                    "payload": {
                        "success": False,
                        "message": "Invalid game ID"
                    }
                })

            if server.get_pid_service().get_profile_from_key(args.get("pid")) is None:
                return json.dumps({
                    "result": "okay",
                    "action": "pregame_info",
                    "payload": {
                        "success": False,
                        "message": "Invalid player ID, please relog."
                    }
                })

            if args.get("result"):
                # They are already done! Wowow!
                match.pregame(result=args.get("result"))
                return json.dumps({
                    "result": "okay",
                    "actions": "pregame_info",
                    "payload": {
                        "success": True,
                        "message": "Pregame info set! Game commencing momentarily."
                    }
                })
            else:
                return json.dumps({
                    "result": "okay",
                    "actions": "pregame_info",
                    "payload": {
                        "success": True,
                        "message": match.pregame()
                    }
                })
        else:
            return json.dumps({
                "result": "okay",
                "action": "pregame_info",
                "payload":{
                    "success": False,
                    "message": "Please provide a game-id to specify game details"
                }
            })
    else:
        # We don't have a pid, so there's literally nothing we can do here. Even if they gave us a gameid.
        return json.dumps({
            "result": "okay",
            "action": "pregame_info",
            "payload":{
                "success": False,
                "message": "Please provide a player-id to specify game details"
            }
        })

@app.route("/get_inventory")
def get_inventory():
    # Return a json representation of the player's inventory. No manipulation possible at this point
    args = request.args
    if args.get("pid"):
        inv_json = server.get_inventory_service().get_inventory(args.get("pid")).to_clean_json()
        to_return = json.dumps({
            "result": "okay",
            "action": "get_inventory",
            "payload": {
                "success": True,
                "message": inv_json
            }
        })
        return to_return
    else:
        return json.dumps({
            "result": "okay",
            "action": "get_inventory",
            "payload": {
                "success": False,
                "message": "Please provide a player-id to see inventory"
            }
        })

@app.route("/use_item")
def use_item():
    args = request.args
    if args.get("pid"):
        if args.get("slot"):
            # We have a pid and a slot. Good deal
            result = server.get_inventory_service().use_item(args.get("pid"), int(args.get("slot")))
            return json.dumps({
                "result": "okay",
                "action": "use_item",
                "payload": {
                    "success": result,
                    "message": "Item used"
                }
            })
        else:
            return json.dumps({
                "result": "okay",
                "action": "use_item",
                "payload": {
                    "success": False,
                    "message": "Please provide a slot-id to use"
                }
            })
    else:
        return json.dumps({
            "result": "okay",
            "action": "use_item",
            "payload": {
                "success": False,
                "message": "Please provide a player-id to use an item"
            }
        })

if __name__ == '__main__':
    app.run(host=server.get_server_configuration().ip, port=5000, debug=False)
