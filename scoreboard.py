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
        scores = db.getTopTeams(
            num=SETTINGS["_scoreboard_size"]
        )  # private settings with _
        scores.insert(0, ["Team Name", "Score"])
        table = GithubFlavoredMarkdownTable(scores)

        msg += f"""
#Top {SETTINGS["_scoreboard_size"]} Team scores 

  <textarea disabled cols=30 rows=7>{table.table}</textarea>

"""

    else:
        msg += f"Scoreboard is set to private\n"

    if SETTINGS["_show_mvp"] == True:
        # top players in the game
        topPlayers = db.topPlayers(num=SETTINGS["_mvp_size"])
        data = [(p.name, p.team.name, v) for p, v in topPlayers]
        data.insert(0, ["Player", "Team", "Score"])
        table = GithubFlavoredMarkdownTable(data)
        msg += f"""
#Top {SETTINGS["_mvp_size"]} Players

<textarea disabled cols=60 rows=10>{table.table}</textarea>
"""
    else:
        msg += f"MVP is set to False    "

    return markdown2.markdown(msg)

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

    # ret = f'{solved_challs}<br>{unsolved_challs}<br>{purchased_hints}'
    scores = db.getTeammateScores(user)
    total = sum([x[1] for x in scores])
    resp = make_response(render_template('scoreboard/hud.html', team_scores=scores, total=total, solved_challs=solved_challs, unsolved_challs=unsolved_challs, purchased_hints=purchased_hints, api_key=api_key))
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
    total_byoc_rewards = db.get_byoc_reward(user)

    return render_template('scoreboard/chall.html', chall=chall, chall_value=chall_value, captured_flags=captured_flags, total_byoc_rewards=total_byoc_rewards purchased_hints=purchased_hints)


@app.get("/")
def index():
    return render_template("scoreboard/index.html")


if __name__ == "__main__":
    app.run(debug=True, port=4000)
