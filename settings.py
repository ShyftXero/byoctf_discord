import diskcache as dc

CACHE_PATH = './byoctf_diskcache'

SETTINGS = dc.Cache(directory=CACHE_PATH)

def init_config():
    config = {  # KEYS THAT START WITH _ ARE CONSIDERED PRIVATE AND DON'T SHOW UP IN THE !status COMMAND
        "ctf_name":         "SOTB BYOCTF",  # your name here. 
        "ctf_start":        -1,             # epoch timestamp UTC; -1 means ignore; https://www.epochconverter.com/
        "ctf_end":          -1,             # epoch timestamp UTC; -1 means ignore
        "ctf_paused":       False,          # is the ctf paused 
        "registration":     "enabled",      # enabled or disabled
        "scoreboard":       "public",       # public or private 
        "_scoreboard_size": 3,              # how many teams to show
        "_show_mvp":        True,           # whether or not to show high scoring
        "_mvp_size":        4,              # how many top scoring players to show
        "_debug":           True,           # interactively enable/disable certain debugging messages 
        '_debug_level':     1,              # allow for some degree of verbosity. 2 is highest so far. 
        "status":           "Operational",  # a generic message; can be updated during the game with ctrl_ctf.py 
        "_firstblood_rate": .1,             # the percentage reward for firstblood solves
        "_decay_solves":     False,          # when decay is invoked. future solves are reduced based on the number of previous solves; best to keep public scoreboard
        "_decay_minimum":      .10,         # minimum percent award. 
        "_botusername":     "BYOCTF_Automaton#7840",             # this is the discordbot's username+discriminator
        '_byoc_reward_rate':    .25         # percentage of a solve that is given back to the author for making the challenge. 
    }

    for k,v in config.items():
        SETTINGS[k] = v


def is_initialized():
    if len( list(SETTINGS.iterkeys()) ) == 0:
        # no data so we need to init
        return False
    return True
    