import diskcache as dc

SETTINGS = dc.Cache(directory='./byoctf_diskcache')

config = {
    "ctf_name":     "Your CTF",     # your name here. 
    "ctf_start":    -1,             # datetime ; -1 means ignore
    "ctf_end":      -1,             # datetime ; -1 means ignore
    "ctf_paused":   False,          # is the ctf paused 
    "registration": "enabled",      # enabled or disabled
    "scoreboard":   "public",       # public or private 
    "status":       "Operational",  # a generic message; can be updated during the game with ctrl_ctf.py 
    
}

def save_settings(): # not needed? as the key is set it is persisted to disk. 
    pass

def load_settings():
    for k,v in config.items():
        SETTINGS[k] = v

def ctf_paused():
    return SETTINGS['ctf_paused']


load_settings()