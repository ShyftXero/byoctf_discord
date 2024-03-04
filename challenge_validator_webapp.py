from rich import print
import database
from byoctf_discord import renderChallenge
from flask import Flask, request, render_template, redirect
from flask_limiter import Limiter
from flask_cors import CORS
from flask_limiter.util import get_remote_address
from loguru import logger
import toml
from settings import SETTINGS

import markdown2

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["3 per second"],
    storage_uri="memory://",
)
CORS(app)
app.secret_key = "thisisasecret"

scoreboard_base_url = 'https://'


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
    print('before')
    logger.debug(request.form)
    chall = request.form.get("toml")
    print(chall)
    print('after')
    challenge_object = parse_chall(chall)
    if type(challenge_object) != dict:
        return challenge_object  

    result = database.validateChallenge(challenge_object)
    
    ret = renderChallenge(result, preview=True)

    return markdown2.markdown(ret)


@app.post('/commit_challenge')
@limiter.limit("4/second", override_defaults=False)
def commit_chall():
    logger.debug(request.form)
    chall = request.form.get("toml")
    api_key = request.form.get("api_key")
    if api_key == None:
        return "api_key not set; set it in the form field", 403
    submitting_user = database.get_user_by_api_key(api_key)
    if submitting_user == None:
        return "user/api_key association not found", 404
    submitting_user = submitting_user.name
    challenge_object = parse_chall(chall)
    if type(challenge_object) != dict:
        return challenge_object

    if submitting_user != challenge_object.get('author'):
        return "Not authorized to submit a challenge on behalf of another user; api_key and username don't match", 403

    result = database.validateChallenge(challenge_object)

    chall_id = database.buildChallenge(result, is_byoc_challenge=True)
    if chall_id == -1:
        msg = f"Insufficient funds for {submitting_user}..."
        if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
                logger.debug(msg)
        return msg, 403

    if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
        logger.debug(f"{submitting_user} created  chall id {chall_id}")
    with database.db_session:
        return redirect(f'/chall/{(database.Challenge[chall_id]).uuid}')


@app.get("/validator")
def index():
    return render_template("validator/index.html")


if __name__ == "__main__":
    app.run(debug=True)
