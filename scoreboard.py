import uuid
from functools import wraps
import hashlib

import markdown2
import time
import toml
from flask import (
    Flask,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from loguru import logger
from rich import print
from terminaltables import AsciiTable, GithubFlavoredMarkdownTable

import database
import database as db
from byoctf_discord import renderChallenge
from settings import SETTINGS
from vis import challs, players, trans

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["50 per second"],
    storage_uri="memory://",
)

CORS(app)
app.secret_key = "thisisasecret"

def ctfRunning():
    if SETTINGS["ctf_paused"]:
        return False

    if (SETTINGS["ctf_start"] == -1 or SETTINGS["ctf_start"] <= time.time()) and (
        SETTINGS["ctf_end"] == -1 or SETTINGS["ctf_end"] >= time.time()
    ):
        return True

    return False

def get_admin_api_key(func):
    @wraps(func)
    def check(*args, **kwargs):
        api_key = request.cookies.get("api_key") 
        
        if api_key == None:
            api_key = request.cookies.get("admin_api_key") 

        if api_key == None:
            return "api_key not set; visit HUD first...", 403
        with db.db_session:
            user = db.get_user_by_api_key(api_key)
            if user == None or user.is_admin == False:
                return "user not found or is not admin", 403
        return func(*args, **kwargs)

    return check


def get_api_key(func):
    @wraps(func)
    def check(*args, **kwargs):
        api_key = request.cookies.get("api_key")
        if api_key == None:
            return "api_key not set; visit HUD first...", 403
        with db.db_session:
            user = db.get_user_by_api_key(api_key)
            if user == None:
                return "user not found", 403
        return func(*args, **kwargs)

    return check

@app.post('/send_tip')
@limiter.limit("100/second", override_defaults=False)
@db.db_session
def send_tip():
    print('send_tip', request.form)
    sender = db.User.get(api_key=request.cookies.get("api_key",'__invalid_api_key__'))
    if sender == None:
        return "api_key invalid", 404
    recipient = db.User.get(name=request.form.get('recipient',"__invalid_recipient__"))
    if recipient == None:
        return "recipient name not found", 404
    amount = float(request.form.get('amount',-1))
    # sender_points = db.getScore(sender)
    # if amount < 0 or amount > sender_points : 
    #     return 'invalid tip amount; too much or too little', 403
    
    res = db.send_tip(sender, recipient, tip_amount=amount, msg=request.form.get('msg'))
    print('db.send_tip returned', res)
    if res[0] == True:
        return f"ok, {res}"
    return str(res)

@app.get("/tip")
@limiter.limit("100/second", override_defaults=False)
@db.db_session
def tip():
    
    user = db.User.get(api_key=request.cookies.get("api_key",'__invalid_api_key__'))
    if user == None:
        return "user not found", 404
    usernames = db.select(u.name for u in db.User if u.name != SETTINGS['_botusername'])[:]
    return render_template('scoreboard/tip.html', users=usernames)



@app.get("/scores")
@limiter.limit("100/second", override_defaults=False)
@db.db_session
def scoreboard():
    msg = ""
    team_scores = list()
    top_players = list()

    if SETTINGS["scoreboard"] == "public":
        # top 3 team scores by default
        team_scores = db.getTopTeams(num=SETTINGS["_scoreboard_size"])
    else:
        return {"error_msg": "Scoreboard is set to private"}

    if SETTINGS["_show_mvp"] == True:
        # top players in the game
        topPlayers = db.topPlayers(num=SETTINGS["_mvp_size"])
        top_players = [(p.name, p.team.name, v) for p, v in topPlayers]

    else:
        msg += f"MVP is set to False    "

    if request.args.get("json") != None:
        ret = {"top_teams": team_scores, "top_players": top_players}
        return ret
    else:
        # return markdown2.markdown(msg)
        return render_template(
            "scoreboard/scores.html",
            msg=msg,
            team_scores=team_scores,
            top_players=top_players,
        )


@app.get("/player/<id>")
@limiter.limit("1/second")
@db.db_session
def get_player(id):
    try:
        player = db.User.get(id=int(id))
    except ValueError as e:
        return e, 405
    if player == None:
        return "player not found", 404

    player_challs = db.get_challs_by_player(player)
    return render_template(
        "scoreboard/player.html", player=player, player_challs=player_challs
    )


# @app.get('/api/all_info')
# @limiter.limit('6/min')
# @db.db_session


@app.get("/admin/net/challenges")
@get_admin_api_key
def net_challenges():
    return challs()


@app.get("/admin/net/players")
@get_admin_api_key
def net_players():
    return players()


@app.get("/admin/net/transactions")
@get_admin_api_key
def net_trans():
    user = request.args.get("user")
    trans_type = request.args.get("trans_type", "tip")
    print(f"getting transactions types {trans_type} for user", user)
    return trans(trans_type=trans_type, user=user)


@app.post("/api/sub_as")
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
    }"""
    payload = request.get_json()
    # print([x for x in payload.items()])

    target_user = payload.get(
        "target_user", "__invalid username here__"
    )  # you can't have a user name with spaces on discord, thus you couldn't have registered one.
    target_user = db.User.get(name=target_user)
    if target_user == None:
        return f"Invalid target_user in payload; {payload.get('target_user')}"
    flag = payload.get("flag", "__not a flag__")
    flag = db.Flag.get(flag=flag)
    if flag == None:
        return f"Invalid flag in payload; {payload.get('flag')}"

    points = payload.get("points")
    if points == None:
        return f"points missing from payload"
    points = float(points)
    message = payload.get("message")
    if message == None:
        return "message missing from payload"
    # did they present anything for the api key?
    api_key = payload.get("admin_api_key")
    if api_key == None:
        return f"admin_api_key missing from payload: {api_key}"
    # does the api key belong to a user?
    admin_user: db.User = db.get_user_by_api_key(api_key)
    if admin_user == None:
        return f"invalid admin api key: {api_key} ;did it change?"

    if admin_user.is_admin == False:
        return {"error": "not an admin"}

    follow_points_rules = payload.get("follow_points_rules", True)

    res = db.createSolve(
        user=target_user,
        flag=flag,
        points_override=points,
        msg=message,
        follow_points_rules=follow_points_rules,
    )

    return {"status": res}

@app.post("/api/manual_reg")
@get_admin_api_key
@limiter.limit("100/second")
@db.db_session
def manual_register():
    """
    register a user manually

    this is the json payload to create a user.
    {
        "username": "TestUser",
        "teamname": "TeamAwesome",
        "teampass": "$0m3L33tPa55",
    }"""
    api_key = request.cookies.get("api_key")
    current_user = db.User.get(api_key=api_key)
    if not current_user:
        msg = "No valid token provided."
        logger.debug(msg)
        return { "status": False, "msg": msg}

    payload = request.get_json()
    username = payload.get("username")
    teamname = payload.get("teamname")
    teampass = payload.get("teampass")

    if not username:
        return { "status": False, "msg": f"username not set" }

    if not teamname:
        return { "status": False, "msg": f"teamname not set" }

    if not teampass:
        return { "status": False, "msg": f"teampass not set" }

    hashed_teampass = hashlib.sha256(teampass.encode()).hexdigest()

    user = db.User.get(name=username)
    if user:
        msg = f"Target user=({user}) already exists!"
        logger.debug(msg)
        return { "status": False, "msg": msg }
    
    # does the team exist?
    team = db.Team.get(name=teamname)
    if team == None:
        team = db.Team(name=teamname, password=hashed_teampass)
        pub, priv = db.generate_keys()
        team.public_key = pub
        team.private_key = priv

    if len(team.members) == SETTINGS["_team_size"]:
        msg = f"No room on the team... currently limited to {SETTINGS['_team_size']} members per team."
        logger.debug(msg)
        return { "status": False, "msg": msg}

    if (hashed_teampass != team.password):  # if it's a new team, these should match automatically..
        msg = f"Password incorrect for team {team.name}"
        logger.debug(f"{username} failed registration; Team {teamname} pass {teampass} hashed {hashed_teampass}")
        return { "status": False, "msg": msg}

    user = db.User(name=username, team=team)
    if team.private_key == "":
        pub, priv = db.generate_keys()
        team.public_key = pub
        team.private_key = priv
    db.commit()
    logger.debug(f"New user=({user.name}) added!")

    with db.db_session:
        user = db.User.get(name=username)
        login_link = f"{SETTINGS['scoreboard_url']}/login/{user.api_key}"
    return {"status": True, "msg": login_link}


@app.get("/api/buy_hint/<hint_uuid>")
@db.db_session
@get_api_key
def buy_hint(hint_uuid):
    """"""
    user = db.get_user_by_api_key(request.cookies.get("api_key",''))
    if user == None:
        return "user api_key not found", 403
    chall = db.Challenge.get(uuid=hint_uuid)
    if chall == None:
        return 'challenge not found', 404

    db.buyHint(user, chall.id)
    
    # resp = make_response(redirect(f'/chall/{hint_uuid}'))
    resp = make_response()
    resp.headers['HX-Refresh'] = 'true'
    return resp

@app.post("/api/grant_points")
@db.db_session
@get_admin_api_key
def grant_points():
    """
    {
        "target_user": "shyft_xero",
        "points": 1337.0,
        "message": "for solving xyz",
        "admin_api_key": "your_api_key"
    }"""
    # authed_user = db.get_user_by_api_key("bot")
    payload = request.form

    target_user = payload.get("target_user")

    if target_user == None:
        return "Invalid target_user in payload", 405
    points = payload.get("points")
    if points == None:
        return "points missing from payload", 405
    points = float(points)
    message = payload.get("message")
    if message == None:
        return "message missing from payload", 405
    # did they present one?
    api_key = payload.get("admin_api_key")
    if api_key == None:
        return "admin_api_key missing from payload", 405
    # did they present the correct one?
    admin_user = db.get_user_by_api_key(api_key)
    if admin_user == None:
        return "invalid admin api key", 403
    if admin_user.is_admin == False:
        return "user is not an admin", 403
    
    # seems legit...
    res = db.grant_points(
        requested_user=target_user, admin_user=admin_user, amount=points, msg=message
    )

    if res:
        return {"status": "sucess", "orig_request": payload}

    else:
        return {"status": "db error", "orig_request": payload}, 400


@app.get("/api/get_team/<target>")
@limiter.limit("1/second")
@db.db_session
def get_team(target):
    if db.is_valid_uuid(target):
        target = uuid.UUID(target)
    else:
        try:
            target = int(target)
        except ValueError:
            return {"error": "invalid id"}

    team: db.Team = db.get_team_by_id(target)
    if team == None:
        return "invalid team id", 403
    ret = {
        "id": team.id,
        "uuid": team.uuid,
        "teamname": team.name,
        # 'teammembers': [ tm.name for tm in db.getTeammates(team)],
        "public_key": team.public_key,
    }
    return ret


@app.get("/api/all_pub_keys")
@limiter.limit("100/second")
@db.db_session
def all_user_pub_keys():
    users = db.select((u.name, u.public_key) for u in db.User)[:]
    teams = db.select((t.name, t.uuid, t.public_key) for t in db.Team)[:]
    ret = {
        "users": [u for u in users],
        "teams": [t for t in teams],
    }
    return ret


@app.get("/api/get_username/<target>")
@limiter.limit("1/second")
@db.db_session
def get_user(target):
    if db.is_valid_uuid(target):
        target = uuid.UUID(target)
    else:
        try:
            target = int(target)
        except ValueError:
            return {"error": "invalid id"}

    user: db.User = db.get_user_by_id(target)
    if user == None:
        return "invalid user id", 403
    ret = {
        "username": user.name,
        "teammates": [tm.name for tm in db.getTeammates(user)],
        "teamname": user.team.name,
        "id": user.id,
        "public_key": user.public_key,
    }
    return ret


@app.get("/login/<api_key>")
@limiter.limit("1/second")
@db.db_session
def login(api_key):
    user = db.get_user_by_api_key(api_key)
    logger.debug(f"api_key:{api_key}, user:{user}")
    if user == None:
        return "invalid api key", 403
    resp = make_response(redirect(url_for("hud")))
    resp.set_cookie("api_key", api_key)
    # resp.set_cookie("api_key", api_key, domain=SETTINGS['ctf_base_domain'])
    return resp


@app.get("/transactions")
@limiter.limit("100/second")
@db.db_session
def get_public_transactions():
    public_transactions = (
        db.select(t for t in db.Transaction)
        .sort_by(lambda t: db.desc(t.time))
        .limit(500)[:]
    )

    return render_template(
        "scoreboard/public_transactions.html", public_transactions=public_transactions
    )


@app.get("/hud")
@app.get("/hud/")
@limiter.limit("100/second", override_defaults=False)
@db.db_session
def hud():
    api_key = request.cookies.get("api_key")
    if api_key == None:
        return "api key not present"

    user = db.get_user_by_api_key(api_key)
    if user == None:
        return "invalid api key", 403
    teamname = user.team.name

    solved_challs: list[db.Challenge] = sorted(
        db.get_completed_challenges(user), key=lambda c: c.title
    )
    unsolved_challs = sorted(db.get_incomplete_challenges(user), key=lambda c: c.title)

    purchased_hints = db.get_team_purchased_hints(user)
    total_byoc_rewards = db.get_byoc_rewards(user)

    # ret = f'{solved_challs}<br>{unsolved_challs}<br>{purchased_hints}'
    scores = db.getTeammateScores(user)
    total = sum([x[1] for x in scores])

    team_byoc_stats = db.get_team_byoc_stats(user)
    usernames = db.select(u.name for u in db.User if u.name != SETTINGS['_botusername'])[:]
    resp = make_response(
        render_template(
            "scoreboard/hud.html",
            teamname=teamname,
            team_scores=scores,
            total=total,
            total_byoc_rewards=total_byoc_rewards,
            solved_challs=solved_challs,
            unsolved_challs=unsolved_challs,
            purchased_hints=purchased_hints,
            api_key=api_key,
            is_admin=user.is_admin,
            team_byoc_stats=team_byoc_stats,
            users=usernames,
        )
    )

    return resp


@app.get("/hud/transactions")
@app.get("/hud/transactions/")
@db.db_session
def transactions():
    api_key = request.cookies.get("api_key")
    if api_key == None:
        return "api_key not set; login first", 400

    user = db.get_user_by_api_key(api_key)
    if user == None:
        return "invalid api key; login first.", 403

    teamname = user.team.name
    transactions = sorted(
        db.get_team_transactions(user), key=lambda t: t.time, reverse=True
    )

    return render_template(
        "scoreboard/transactions.html",
        api_key=api_key,
        transactions=transactions,
        teamname=teamname,
    )


@app.get("/challenges")
@limiter.limit("100/second", override_defaults=False)
@db.db_session
def challenges():
    if not ctfRunning():
        return render_template(
            "scoreboard/challenges.html",
            parsed=[],
            available_challenges=[],
        )

    api_key = request.cookies.get("api_key")
    if api_key == None:
        return "api_key not set; visit HUD first...", 403
    user = db.User.get(api_key=api_key)
    if user == None:
        return "invalid user api_key", 403

    available_challenges = db.get_unlocked_challenges(user)
    teammates = db.getTeammates(user)
    parsed = [
        (
            c.id,
            c.uuid,
            c.author.name,
            c.title,
            db.challValue(c),
            f"{db.percentComplete(c, user)}%",
            "*" * int(db.avg(r.value for r in db.Rating if r.challenge == c) or 0),
            ", ".join([t.name for t in c.tags]),
        )
        for c in available_challenges
        if c.id > 0 and c.author not in teammates and c.title != "__bonus__"
    ]
    return render_template(
        "scoreboard/challenges.html",
        parsed=parsed,
        available_challenges=available_challenges,
    )


@app.get("/chall/<chall_uuid>")
@limiter.limit("100/second", override_defaults=False)
@db.db_session
def chall(chall_uuid):
    chall = db.Challenge.get(uuid=chall_uuid)
    if chall == None:
        return "invalid challenge uuid", 404

    api_key = request.cookies.get("api_key")
    if api_key == None:
        return "api_key not set; visit HUD first..."
    # user = db.get_user_by_api_key(api_key)
    user = db.User.get(api_key=api_key)
    if user == None:
        return "invalid api key", 403

    purchased_hints = db.get_team_purchased_hints(user, chall_id=chall.id)
    chall_value = db.challValue(chall)
    captured_flags = sorted(
        db.getSubmittedChallFlags(chall, user), key=lambda f: f.value
    )
    solves = db.getSolves(chall)

    teammates = db.getTeammates(user)

    if chall.author in teammates:
        team_owned_challenge = True
    else:
        team_owned_challenge = False

    rendered_chall_description = db.render_variables(user, chall.description)
    next_hint_cost = db.getHintCost(user, chall.id)

    return render_template(
        "scoreboard/chall.html",
        api_key=api_key,
        chall=chall,
        team_owned_challenge=team_owned_challenge,
        chall_value=chall_value,
        captured_flags=captured_flags,
        purchased_hints=purchased_hints,
        next_hint_cost=next_hint_cost,
        solves=solves,
        rendered_chall_description=rendered_chall_description,
    )


@app.route("/sub", methods=["GET", "POST"])
@limiter.limit("100/second", override_defaults=False)
@db.db_session
@get_api_key
def submit_flag():
    if not ctfRunning():
        return "ctf not running."

    if request.method == "POST":
        user: db.User = db.get_user_by_api_key(request.cookies.get("api_key"))
        flag = request.form.get("flag")
        if flag == None or user == None:
            return "flag or user missing from request; try setting api_key cookie", 405

        submisssion_result = db.submit_flag(user_str=user.name, flag_str=flag)
        if submisssion_result == False:
            return "incorrect flag", 404

        if submisssion_result == "":
            submisssion_result = "invalid submission"

        return f"{submisssion_result}"

    return render_template("scoreboard/submit.html")


@app.get("/")
def scoreboard_index():
    return render_template("scoreboard/index.html")


@app.get("/create")
def create():
    return render_template("creator/creator.html")


def parse_chall(chall):
    try:
        return toml.loads(chall)
    except toml.TomlDecodeError as e:
        print(f"error decoding toml: {e}")
        return f"error decoding toml: {e}", 500
    except TypeError as e:
        print(f"error parsing toml: {e}")
        return f"error parsing toml: {e}", 500
    except BaseException as e:
        print(e)
        return f"{e}", 500


@app.post("/validate")
# @limiter.limit("4/second", override_defaults=False)
def validate():
    print("before")
    logger.debug(request.form)
    chall = request.form.get("toml")
    print(chall)
    print("after")
    challenge_object = parse_chall(chall)
    if type(challenge_object) != dict:
        return challenge_object

    result = database.validateChallenge(challenge_object)

    ret = renderChallenge(result, preview=True)

    return markdown2.markdown(ret)


@app.post("/commit_challenge")
@limiter.limit("4/second", override_defaults=False)
def commit_chall():
    logger.debug(request.form)
    chall = request.form.get("toml")
    api_key = request.cookies.get("api_key")
    if api_key == None:
        return "api_key not set; set it in the form field", 401
    submitting_user = database.get_user_by_api_key(api_key)
    if submitting_user == None:
        return "user/api_key association not found", 404
    submitting_user = submitting_user.name
    challenge_object = parse_chall(chall)
    if type(challenge_object) != dict:
        return challenge_object

    if submitting_user != challenge_object.get("author"):
        return (
            "Not authorized to submit a challenge on behalf of another user; api_key and username don't match",
            403,
        )

    result = database.validateChallenge(challenge_object)
    if result.get('valid') == False:
        return f"invalid challenge_object; {result}", 400

    chall_id = database.buildChallenge(result, is_byoc_challenge=True)
    if chall_id == -3:
        msg = f"Insufficient funds for {submitting_user}..."
        return msg, 403
    elif chall_id == -2:
        msg = f'author does not exist: {submitting_user}' # shouldn't ever get here because of line 575 
    elif chall_id == -1:
        msg = f'challenge itself not valid for somereason; {result}'
    if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
        logger.debug(msg)

    if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
        logger.debug(f"{submitting_user} created  chall id {chall_id}")


    with database.db_session:
        chall_uuid = (database.Challenge[chall_id]).uuid
        chall_url = f"/chall/{chall_uuid}"
    ret = f"cool. here's your challenge -> <a href='{chall_url}'>{chall_uuid}</a>"
    return ret


@app.get("/validator")
def validator_index():
    return render_template("validator/index.html")


if __name__ == "__main__":
    app.run(debug=True, port=4000)
