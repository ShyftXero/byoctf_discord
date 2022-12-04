from rich import print
import database as db
from settings import SETTINGS
from flask import Flask, request, render_template
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


@app.get("/")
def index():
    return render_template("scoreboard/index.html")


if __name__ == "__main__":
    app.run(debug=True, port=4000)
