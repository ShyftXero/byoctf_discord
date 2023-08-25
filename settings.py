import diskcache as dc

CACHE_PATH = "./byoctf_diskcache"

SETTINGS = dc.Cache(directory=CACHE_PATH)


def default_config():
    config = {  # KEYS THAT START WITH _ ARE CONSIDERED PRIVATE AND DON'T SHOW UP IN THE !status COMMAND
        "ctf_name": "SOTB BYOCTF",  # your name here.
        "ctf_start": -1,  # epoch timestamp UTC; -1 means ignore; https://www.epochconverter.com/
        "ctf_end": -1,  # epoch timestamp UTC; -1 means ignore
        "ctf_paused": False,  # is the ctf paused
        "registration": "enabled",  # enabled or disabled
        "scoreboard": "public",  # public or private
        "_scoreboard_size": 3,  # how many teams to show
        "_team_size": 4,  # max team members
        "_show_mvp": True,  # whether or not to show high scoring
        "_mvp_size": 4,  # how many top scoring players to show
        "_debug": True,  # interactively enable/disable certain debugging messages
        "_debug_level": 1,  # allow for some degree of verbosity. 2 is highest so far.
        "status": "Operational",  # a generic message; can be updated during the game with ctrl_ctf.py,
        "percent_solved_to_unlock": .5, # this is the minimum percentage of parent chall flags must be captured to determine if a challenge is unlocked. 
        "_logfile": "byoctf.log",  # logfile for debugging/tail -f or whatever
        
        #sqlite config
        # "_db_type": "sqlite",  # sqlite is easy and works well enough. I probably won't leverage the others.; that being said, hosted cockroach or postgres is also easy...
        # "_db_user": "username1",  # db username
        # "_db_pass": "password1",  # db password
        # "_db_database": "byoctf.db",  # if using mysql or postgres, this is the db to utilize. If using sqlite, this is the file to store stuff in.
        
        #postgres config
        "_db_type": "postgres",  # sqlite is easy and works well enough. I probably won't leverage the others.; that being said, hosted cockroach or postgres is also easy...
        "_db_host": "drona.db.elephantsql.com",  # database host
        "_db_user": "acmmdipm",  # db username
        "_db_pass": "DP7wvxE8NQHfNJDckr23DXDr0rChq02m",  # db password
        
        "_db_database": "acmmdipm",  # if using mysql or postgres, this is the db to utilize. If using sqlite, this is the file to store stuff in.
        
        
        "_ctf_guild_id": 618912342385885198,  # your discord server. user right-click copy ID to get these
        "_ctf_channel_id": 735581872259727435,  # channel ID to give to users once they register.
        "_ctf_channel_role_id": 735582054485328004,  # the ID of the role which will be given to players as they register; makes the channel visible to them.
        "_firstblood_rate": 0.1,  # the percentage reward for firstblood solves
        "_decay_solves": False,  # when decay is invoked. future solves are reduced based on the number of previous solves; best to keep public scoreboard
        "_decay_minimum": 0.10,  # minimum percent award.
        "_botusername": "BYOCTF_Automaton#7840",  # this is the discordbot's username+discriminator; leaving as of 20230721 because it seems to be working... 
        "_byoc_reward_rate": 0.25,  # percentage of a solve that is given back to the author for making the challenge.
        "_byoc_commit_fee": 0.5,  # percentage of challenge value to charge author to post a BYOC challenge
        "_byoc_max_reward": 2.0,  # maximux return for creating a challenge. # 08OCT22 I still want to leverage other tools than this one as I believe the challenge market can behave itself.
        "_byoc_chall_min_val": 100,  # minimum value for byoc chall to be considered valid
        "_byoc_hint_reward_rate": 0.1,  # how much of a tip should be given to the challenge author.
        "_rate_limit_window": 2,  # 2 second cooldown time; 1 submission every 2 seconds per player.  requires restart
        "rating_min": 1,  # min value for rating system
        "rating_max": 9,  # max value for rating system
    }

    return config


def init_config():
    config = default_config()
    for k, v in config.items():
        SETTINGS[k] = v


def is_initialized():
    starting_config = default_config()

    for k in starting_config.keys():
        if k not in list(SETTINGS.iterkeys()):
            print(f"{k} is missing... run ./ctrl_ctf.py init_config")
            return False
    return True


is_initialized()
