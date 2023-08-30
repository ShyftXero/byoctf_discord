from rich import print
import database as db
from settings import SETTINGS
from flask import Flask, request, render_template, make_response, url_for, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

from terminaltables import AsciiTable, GithubFlavoredMarkdownTable

import markdown2

from loguru import logger

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
@limiter.limit("20/second", override_defaults=False)
@db.db_session
def scoreboard():
    

    msg = ""
    team_scores = list()
    top_players = list()



    if SETTINGS["scoreboard"] == "public":
        # top 3 team scores by default
        team_scores = db.getTopTeams(num=SETTINGS["_scoreboard_size"])  
    else:
        return {'error_msg':"Scoreboard is set to private"}

    
    if SETTINGS["_show_mvp"] == True:
        # top players in the game
        topPlayers = db.topPlayers(num=SETTINGS["_mvp_size"])
        top_players = [(p.name, p.team.name, v) for p, v in topPlayers]
        
    else:
        msg += f"MVP is set to False    "
    
    if request.args.get('json') != None:
        ret = {
            "top_teams": team_scores,
            "top_players": top_players
        }
        return ret
    else:
        # return markdown2.markdown(msg)
        return render_template('scoreboard/scores.html', msg=msg, team_scores=team_scores, top_players=top_players)

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
    payload = request.get_json()
    # print([x for x in payload.items()])
    
    
    target_user = payload.get('target_user', "__invalid username here__") # you can't have a user name with spaces on discord, thus you couldn't have registered one. 
    target_user = db.User.get(name=target_user)
    if target_user == None:
        return f"Invalid target_user in payload; {payload.get('target_user')}" 
    flag = payload.get('flag', "__not a flag__")
    flag = db.Flag.get(flag=flag)
    if flag == None: 
        return f"Invalid flag in payload; {payload.get('flag')}"

    points = payload.get('points')
    if points == None:
        return f"points missing from payload"
    points = float(points)
    message = payload.get('message')
    if message == None:
        return "message missing from payload"
    # did they present anything for the api key? 
    api_key = payload.get('admin_api_key')
    if api_key == None:
        return f"admin_api_key missing from payload: {api_key}"
    # does the api key belong to a user?
    admin_user:db.User = db.get_user_by_api_key(api_key)
    if admin_user == None:
        return f"invalid admin api key: {api_key} ;did it change?"

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
        return "invalid admin api key", 403
    
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
        return "invalid user id", 403
    ret = {
        "username": user.name,
        'teammates': [ tm.name for tm in db.getTeammates(user)],
        'teamname': user.team.name
    }
    return ret


@app.get('/login/<api_key>')
@limiter.limit("1/second")
@db.db_session
def login(api_key):

    user = db.get_user_by_api_key(api_key)
    logger.debug(f"api_key{api_key}, user:{user}")
    if user == None:
        return "invalid api key", 403
    resp = make_response(redirect(url_for('hud')))
    resp.set_cookie('api_key', api_key)
    return resp

@app.get('/hud')
@app.get('/hud/')
@limiter.limit("5/second", override_defaults=False)
@db.db_session
def hud():
    api_key = request.cookies.get('api_key')
    if api_key == None:
        return "api key not present"
        
        
    user = db.get_user_by_api_key(api_key)
    if user == None:
        return "invalid api key", 403
    teamname=user.team.name
    
    solved_challs:list[db.Challenge] = sorted(db.get_completed_challenges(user), key=lambda c: c.title)
    unsolved_challs = sorted(db.get_incomplete_challenges(user), key=lambda c: c.title)
    
    
    purchased_hints = db.get_team_purchased_hints(user)
    total_byoc_rewards = db.get_byoc_rewards(user)

    # ret = f'{solved_challs}<br>{unsolved_challs}<br>{purchased_hints}'
    scores = db.getTeammateScores(user)
    total = sum([x[1] for x in scores])


    team_byoc_stats = db.get_team_byoc_stats(user)

    resp = make_response(render_template('scoreboard/hud.html', teamname=teamname, team_scores=scores, total=total,  total_byoc_rewards=total_byoc_rewards, solved_challs=solved_challs, unsolved_challs=unsolved_challs, purchased_hints=purchased_hints, api_key=api_key, team_byoc_stats=team_byoc_stats))

    
    return resp


@app.get('/hud/transactions')
@app.get('/hud/transactions/')
@db.db_session
def transactions():
    api_key = request.cookies.get('api_key')
    if api_key == None:
        return "api_key not set; login first", 400

    user = db.get_user_by_api_key(api_key)
    if user == None:
        return "invalid api key; login first.", 403

    teamname = user.team.name
    transactions = sorted(db.get_team_transactions(user), key=lambda t: t.time, reverse=True)

    return render_template('scoreboard/transactions.html', api_key=api_key, transactions=transactions, teamname=teamname)



@app.get('/chall/<chall_uuid>')
@limiter.limit("5/second", override_defaults=False)
@db.db_session
def chall(chall_uuid):
    chall = db.Challenge.get(uuid=chall_uuid)
    if chall == None:
        return "invalid challenge uuid", 404
    
    api_key = request.cookies.get('api_key')
    if api_key == None:
        return "api_key not set; visit HUD first..."
    # user = db.get_user_by_api_key(api_key)
    user = db.User.get(api_key=api_key)
    if user == None:
        return "invalid api key", 403
    
    purchased_hints = db.get_team_purchased_hints(user, chall_id=chall.id)
    chall_value= db.challValue(chall)
    captured_flags = sorted(db.getSubmittedChallFlags(chall, user), key=lambda f: f.value)
    solves = db.getSolves(chall)

    teammates = db.getTeammates(user)

    if chall.author in teammates:
        team_owned_challenge = True
    else:
        team_owned_challenge = False

        

    return render_template('scoreboard/chall.html', api_key=api_key, chall=chall,  team_owned_challenge=team_owned_challenge,chall_value=chall_value, captured_flags=captured_flags, purchased_hints=purchased_hints, solves=solves)


@app.get("/")
def index():
    return render_template("scoreboard/index.html")


if __name__ == "__main__":
    app.run(debug=True, port=4000)
