import diskcache as dc



CACHE_PATH = './byoctf_diskcache'

SETTINGS = dc.Cache(directory=CACHE_PATH)

def init_config():
    config = {  # KEYS THAT START WITH _ ARE CONSIDERED PRIVATE AND DON'T SHOW UP IN THE !status COMMAND
        "ctf_name":         "Your CTF",     # your name here. 
        "ctf_start":        -1,             # datetime ; -1 means ignore
        "ctf_end":          -1,             # datetime ; -1 means ignore
        "ctf_paused":       False,          # is the ctf paused 
        "registration":     "enabled",      # enabled or disabled
        "scoreboard":       "public",       # public or private 
        "_scoreboard_size": 3,              # how many teams to show
        "_show_mvp":        True,           # whether or not to show high scoring
        "_mvp_size":        4,              # how many top scoring players to show
        "status":           "Operational",  # a generic message; can be updated during the game with ctrl_ctf.py 
    }

    for k,v in config.items():
        SETTINGS[k] = v


def is_initialized():
    if len( list(SETTINGS.iterkeys()) ) == 0:
        # no data so we need to init
        return False
    return True
    