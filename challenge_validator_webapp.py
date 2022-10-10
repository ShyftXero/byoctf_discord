from rich import print
import database
from byoctf_discord import renderChallenge
from flask import Flask, request, render_template
from loguru import logger
import toml

app = Flask(__name__)
app.secret_key = "thisisasecret"


@app.post("/validate")
def validate():

    try:
        challenge_object = toml.loads(request.form.get("challenge"))
    except toml.TomlDecodeError as e:
        print(e)
        return f"{e}"

    result = database.validateChallenge(challenge_object)
    logger.debug(challenge_object)

    ret = renderChallenge(result, preview=True)
    ret += "<br><br>"
    ret += "raw:"
    ret += "<br>"
    ret += f"{challenge_object}"
    print(ret)
    return ret


@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
