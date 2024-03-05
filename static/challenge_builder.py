# this is meant to be run via pyscript as part of the challenge builder web app

import toml

# import js
import uuid
from js import document

# import base64

import pyodide_http
pyodide_http.patch_all()
import requests

from js import Uint8Array, File, URL, document
import io
from pyodide.ffi.wrappers import add_event_listener

num_flags = 1
num_hints = 1

flag_html_template = """
<div class="card card-body" id="flag_set_XXX">
    Flag: XXX
    <p>
        Flag Title:<input type="text" class="form-control flag" name="flag_XXX_title" id="flag_XXX_title" placeholder="Flag description for display; this may be visible to players">
        Flag Value:<input type="text" class="form-control flag" name="flag_XXX_value" id="flag_XXX_value" placeholder="How many points is THIS flag worth?">
        Actual Flag:<input type="text" class="form-control flag" name="flag_XXX_flag" id="flag_XXX_flag" placeholder="This is the actual flag as a player would submit it e.g. FLAG{good_job_solving}">
    </p>
    <button onclick='document.getElementById("flag_set_XXX").parentNode.parentNode.removeChild(document.getElementById("flag_set_XXX").parentNode)'>Delete</button>
</div>
"""

hint_html_template = """
<div class="card card-body" id="hint_set_XXX">
    Hint: XXX
    <p>
        Hint Cost:<input type="text" class="form-control hint" name="hint_XXX_cost" id="hint_XXX_cost" placeholder="How much will a player have to pay to view this hint?">
        Hint text:<textarea class="form-control hint" name="hint_XXX_text" id="hint_XXX_text" rows="2" width="100%" placeholder="This is the actual hint you are providing..."></textarea>
    </p>
    <button onclick='document.getElementById("hint_set_XXX").parentNode.parentNode.removeChild(document.getElementById("hint_set_XXX").parentNode)'>Delete</button>
</div>
"""


class hashabledict(dict):
    def __key(self):
        return tuple((k, self[k]) for k in sorted(self))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return self.__key() == other.__key()


def collect_flags():
    flags = list()
    # print('here')
    for i in range(1, 1000):
        # print(i)
        try:  # these divs may not exists if they were deleted
            title = document.getElementById(f"flag_{i}_title")
            value = document.getElementById(f"flag_{i}_value")
            flag = document.getElementById(f"flag_{i}_flag")
        except AttributeError as e:
            continue  # carry on
        # print('flag values', title.value, value.value, flag.value)
        try:
            if title.value == None or value.value == None or flag.value == None:
                continue
            flag_points = int(value.value.strip())
            tmp = hashabledict(
                {
                    "flag_title": title.value.strip(),
                    "flag_value": flag_points,
                    "flag_flag": flag.value.strip(),
                }
            )
            flags.append(tmp)
            # print(flags)

        except AttributeError as e:
            continue
        except ValueError as e:
            continue

    return list(set(flags))


def collect_hints():
    hints = list()
    for i in range(1, 1000):
        # print(i)
        try:
            cost = document.getElementById(f"hint_{i}_cost")
            text = document.getElementById(f"hint_{i}_text")
        except AttributeError as e:
            continue
        # print('hint values', cost.value, text.value)
        try:
            if cost.value == None or text.value == None:
                continue
            cost = int(cost.value.strip())
            tmp = hashabledict({"hint_cost": cost, "hint_text": text.value.strip()})
            hints.append(tmp)
            # print(hints)
        except AttributeError as e:
            continue
        except ValueError as e:
            continue

    return list(set(hints))


def add_flag(event):
    global num_flags
    # print(f'adding a flag, {num_flags} total' )

    this_flag_html = flag_html_template.replace("XXX", str(num_flags))
    this_flag_div = document.createElement("div")
    this_flag_div.innerHTML = this_flag_html
    flag_div = document.getElementById("flag_div")
    flag_div.appendChild(this_flag_div)
    num_flags += 1


def add_hint(event):
    global num_hints
    # print(f'adding a hint, {num_hints} total' )

    this_hint_html = hint_html_template.replace("XXX", str(num_hints))
    this_hint_div = document.createElement("div")
    this_hint_div.innerHTML = this_hint_html
    flag_div = document.getElementById("hint_div")
    flag_div.appendChild(this_hint_div)
    num_hints += 1




def build_challenge(event):

    tags = list(
        set(
            [
                x
                for x in document.getElementById('tags').value.replace(" ", "").lower().split(",")
                if x != ""
            ]
        )
    )
    depends_on = list(
        set(
            [
                x
                for x in document.getElementById("depends_on").value.replace(" ", "").lower().split(",")
                if x != ""
            ]
        )
    )

    challenge_object = {
        "author": document.getElementById("author").value.strip(),
        "challenge_title": document.getElementById("challenge_title").value.strip(),
        "uuid": str(uuid.uuid4()),
        "challenge_description": document.getElementById("challenge_description").value.strip(),
        "tags": tags,
        "depends_on": depends_on,
        "flags": collect_flags(),
        "hints": collect_hints(),
    }

    ret = toml.dumps(challenge_object)
    # print('successfully dumped')

    output = document.getElementById("tomlDiv")
    output.innerHTML = ret

    return ret

def validate_challenge(event):
    chall_toml = build_challenge(None)

    payload = {"toml": chall_toml}

    raw = document.location.href.split('/')
    current_url = f'{raw[0]}//{raw[2]}'
    print(f'{current_url=}')

    # print(chall_toml)
    # resp = requests.post('http://localhost:5000/validate', data=payload) # dev
    resp = requests.post(f"{current_url}/validate", data=payload)  # prod
    # print('sent post')
    output = document.getElementById("validateDiv")
    output.innerHTML = resp.text
    # print(resp.text)
    output = document.getElementById("tomlDiv")
    output.innerHTML = ''
    return



def download_challenge(event):
    data = build_challenge(None)
    encoded_data = data.encode("utf-8")
    my_stream = io.BytesIO(encoded_data)

    js_array = Uint8Array.new(len(encoded_data))
    js_array.assign(my_stream.getbuffer())

    title = "_".join(document.getElementById("challenge_title").value.strip().split(" "))
    if title == "":
        title = "challenge"
    file_name = f"{title}.toml"
    file = File.new([js_array], file_name, {type: "text/plain"})
    url = URL.createObjectURL(file)

    hidden_link = document.createElement("a")
    hidden_link.setAttribute("download", file_name)
    hidden_link.setAttribute("href", url)
    hidden_link.click()


if __name__ == '__main__':
    add_flag(None)
    add_hint(None)