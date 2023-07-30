from rich import print
import database as db
from settings import SETTINGS
from flask import Flask, request, render_template, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

from terminaltables import AsciiTable, GithubFlavoredMarkdownTable

import markdown2

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["3 per second"],
    storage_uri="memory://",
)

CORS(app)
app.secret_key = "thisisasecret"


@app.get("/scores")
@limiter.limit("3/second", override_defaults=False)
@db.db_session
def scoreboard():
    

    msg = ""

    if SETTINGS["scoreboard"] == "public":
        # top 3 team scores
        team_scores = db.getTopTeams(
            num=SETTINGS["_scoreboard_size"]
        )  # private settings with _
        team_scores.insert(0, ["Team Name", "Score"])
        table = GithubFlavoredMarkdownTable(team_scores)

        msg += f"""
#Top {SETTINGS["_scoreboard_size"]} Team scores 

  <textarea disabled cols=30 rows=7>{table.table}</textarea>

"""

    else:
        msg += f"Scoreboard is set to private\n"

    if SETTINGS["_show_mvp"] == True:
        # top players in the game
        topPlayers = db.topPlayers(num=SETTINGS["_mvp_size"])
        player_data = [(p.name, p.team.name, v) for p, v in topPlayers]
        player_data.insert(0, ["Player", "Team", "Score"])
        table = GithubFlavoredMarkdownTable(player_data)
        msg += f"""
#Top {SETTINGS["_mvp_size"]} Players

<textarea disabled cols=60 rows=10>{table.table}</textarea>
"""
    else:
        msg += f"MVP is set to False    "
    
    if request.args.get('json') != None:
        ret = {
            "top_teams": team_scores,
            "top_players": player_data
        }
        return ret
    else:
        return markdown2.markdown(msg)

@app.post('/api/sub_as')
@limiter.limit("1/second")
@db.db_session
def create_solve():
    """
    see database.py createSolve
    The createSolve function attempts to create the transaction that awards points and fails if certain criteria aren't met. Its core purpose was to prevent players from submitting their own flags, their teammates flags, or flags they've already captured. It's also how the decaying points and first blood bonus and BYOC payouts are awarded (if applicable). 

    points_override is to allow admins to manually specify points when creating the solve. 

    this is the json payload to create a solve by submitting a flag on their behalf. 
    {
        "target_user": "shyft_xero",
        "flag": "FLAG{abc_xyz}", 
        "points": 1337.0,
        "message": "for solving xyz",
        "admin_api_key": "your_api_key"
        "follow_points_rules": true
    }
"""
    payload = request.form
    
    
    target_user = payload.get('target_user', "__invalid username here__") # you can't have a user name with spaces on discord, thus you couldn't have registered one. 
    target_user = db.User.get(name=target_user)
    if target_user == None:
        return "Invalid target_user in payload" 
    flag = payload.get('flag', "__not a flag__")
    flag = db.Flag.get(flag=flag)
    if flag == None: 
        return "Invalid flag in payload"

    points = payload.get('points')
    if points == None:
        return "points missing from payload"
    points = float(points)
    message = payload.get('message')
    if message == None:
        return "message missing from payload"
    # did they present anything for the api key? 
    api_key = payload.get('admin_api_key')
    if api_key == None:
        return "admin_api_key missing from payload"
    # does the api key belong to a user?
    admin_user:db.User = db.get_user_by_api_key(api_key)
    if admin_user == None:
        return "invalid admin api key"

    follow_points_rules = payload.get('follow_points_rules', True)

    res = db.createSolve(user=target_user, flag=flag, points_override=points, msg=message, follow_points_rules=follow_points_rules)

    return {"status": res }


@app.post('/api/grant_points')
@db.db_session
def grant_points():
    """
    {
        "target_user": "shyft_xero",
        "points": 1337.0,
        "message": "for solving xyz",
        "api_key": "your_api_key"
    }
"""
    # authed_user = db.get_user_by_api_key("bot")
    payload = request.form
    
    target_user = payload.get('target_user')
    
    if target_user == None:
        return "Invalid target_user in payload" 
    points = payload.get('points')
    if points == None:
        return "points missing from payload"
    points = float(points)
    message = payload.get('message')
    if message == None:
        return "message missing from payload"
    # did they present one? 
    api_key = payload.get('admin_api_key')
    if api_key == None:
        return "admin_api_key missing from payload"
    # did they present the correct one?
    admin_user = db.get_user_by_api_key(api_key)
    if admin_user == None:
        return "invalid admin api key"
    
    # seems legit...
    res = db.grant_points(user=target_user,admin_user=admin_user, amount=points, msg=message)
    
    if res:
        return {'status':"sucess", "orig_request":payload}
    
    else:
        return {"status":"db error", "orig_request":payload}

@app.get('/api/get_username/<int:uid>')
@limiter.limit("1/second")
@db.db_session
def get_user(uid):
    user:db.User = db.get_user_by_id(uid)
    if user == None:
        return "invalid user id"
    ret = {
        "username": user.name,
        'teammates': [ tm.name for tm in db.getTeammates(user)],
        'teamname': user.team.name
    }
    return ret



@app.get('/hud/<api_key>')
@limiter.limit("5/second", override_defaults=False)
@db.db_session
def hud(api_key):
    user = db.get_user_by_api_key(api_key)
    if user == None:
        return "invalid api key"
    
    solved_challs:list[db.Challenge] = db.get_all_challenges(user)
    
    unsolved_challs = db.get_unsolved_challenges(user)
    purchased_hints = db.get_purchased_hints(user)
    total_byoc_rewards = db.get_byoc_rewards(user)

    # ret = f'{solved_challs}<br>{unsolved_challs}<br>{purchased_hints}'
    scores = db.getTeammateScores(user)
    total = sum([x[1] for x in scores])


    resp = make_response(render_template('scoreboard/hud.html', team_scores=scores, total=total,  total_byoc_rewards=total_byoc_rewards, solved_challs=solved_challs, unsolved_challs=unsolved_challs, purchased_hints=purchased_hints, api_key=api_key))
    resp.set_cookie('api_key', api_key)
    return resp

@app.get('/chall/<chall_uuid>')
@limiter.limit("5/second", override_defaults=False)
@db.db_session
def chall(chall_uuid):
    chall = db.Challenge.get(uuid=chall_uuid)
    if chall == None:
        return "invalid challenge uuid"
    
    api_key = request.cookies.get('api_key')
    if api_key == None:
        return "api_key not set; visit HUD first..."
    # user = db.get_user_by_api_key(api_key)
    user = db.User.get(api_key=api_key)
    if user == None:
        return "invalid api key"
    
    purchased_hints = db.get_purchased_hints(user, chall_id=chall.id)
    chall_value= db.challValue(chall)
    captured_flags = db.getSubmittedChallFlags(chall, user)
    

    return render_template('scoreboard/chall.html', api_key=api_key, chall=chall, chall_value=chall_value, captured_flags=captured_flags, purchased_hints=purchased_hints)


@app.get("/")
def index():
    return render_template("scoreboard/index.html")


if __name__ == "__main__":
    app.run(debug=True, port=4000)
