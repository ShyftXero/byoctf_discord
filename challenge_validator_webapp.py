from rich import print
import database
from byoctf_discord import renderChallenge
from flask import Flask, request, render_template
from flask_limiter import Limiter
from flask_cors import CORS
from flask_limiter.util import get_remote_address
from loguru import logger
import toml

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

@app.get("/create")
def create():
    return render_template('creator/creator.html')

@app.post("/validate")
@limiter.limit("2/second", override_defaults=False)
def validate():

    try:
        # print(f'{request.form}')
        challenge_object = toml.loads(request.form.get("toml"))
    except toml.TomlDecodeError as e:
        print(e)
        return f"error decoding toml: {e}"
    except TypeError as e:
        print(e)
        return f'error parsing toml: {e}'

    result = database.validateChallenge(challenge_object)
    logger.debug(challenge_object)

    ret = renderChallenge(result, preview=True)

    return markdown2.markdown(ret)


@app.get("/")
def index():
    return render_template("validator/index.html")


if __name__ == "__main__":
    app.run(debug=True)
