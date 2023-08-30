# this is meant to be run via pyscript as part of the challenge builder web app

import toml

# import js
import uuid
from pyscript import Element
from js import document
# import base64

import pyodide_http
pyodide_http.patch_all()
import requests

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
    return tuple((k,self[k]) for k in sorted(self))
  def __hash__(self):
    return hash(self.__key())
  def __eq__(self, other):
    return self.__key() == other.__key()

def collect_flags():
	flags = list()
	#print('here')
	for i in range(1,1000):
		#print(i)
		try: #these divs may not exists if they were deleted
			title = Element(f'flag_{i}_title')
			value = Element(f'flag_{i}_value')
			flag = Element(f'flag_{i}_flag')
		except AttributeError as e:
			continue # carry on
		#print('flag values', title.value, value.value, flag.value)
		try:
			if title.value == None or value.value == None or flag.value == None: 
				continue
			flag_points = int(value.value.strip())
			tmp = hashabledict({
				'flag_title': title.value.strip(),
				'flag_value': flag_points,
				'flag_flag' : flag.value.strip()
			})
			flags.append(tmp)
			#print(flags)

		except AttributeError as e:
			continue	
		except ValueError as e:
			continue

	return list(set(flags))

def collect_hints():
	hints = list()
	for i in range(1,1000):
		#print(i)
		try:
			cost = Element(f'hint_{i}_cost')
			text = Element(f'hint_{i}_text')
		except AttributeError as e:
			continue
		#print('hint values', cost.value, text.value)
		try:
			if cost.value == None or text.value == None :
				continue
			cost = int(cost.value.strip())
			tmp = hashabledict({
				'hint_cost': cost ,
				'hint_text': text.value.strip()
			})
			hints.append(tmp)
			#print(hints)
		except AttributeError as e:
			continue
		except ValueError as e:
			continue
		
	return list(set(hints))	


def add_flag():
	global num_flags
	# print(f'adding a flag, {num_flags} total' )
	
	this_flag_html = flag_html_template.replace("XXX", str(num_flags))
	this_flag_div = document.createElement("div")
	this_flag_div.innerHTML = this_flag_html
	flag_div = document.getElementById('flag_div')
	flag_div.appendChild(this_flag_div)
	num_flags += 1
	
	

def add_hint():
	global num_hints
	# print(f'adding a hint, {num_hints} total' )
	
	this_hint_html = hint_html_template.replace("XXX", str(num_hints))
	this_hint_div = document.createElement("div")
	this_hint_div.innerHTML = this_hint_html
	flag_div = document.getElementById('hint_div')
	flag_div.appendChild(this_hint_div)
	num_hints += 1

def validate_challenge():
	chall_toml = build_challenge()

	payload = {
		"toml": chall_toml
	}
	
	# print(chall_toml)
	# resp = requests.post('http://localhost:5000/validate', data=payload) # dev
	resp = requests.post('https://validator.byoctf.com/validate', data=payload) # prod
	# print('sent post')
	output = Element('validateDiv')
	output.element.innerHTML = resp.text
	# print(resp.text)
	return

def build_challenge():
	tags = list(set([x for x in Element('tags').value.replace(' ','').lower().split(',') if x != '']))
	depends_on = list(set([x for x in Element('depends_on').value.replace(' ','').lower().split(',') if x != '']))

	challenge_object = {
		'author': Element("author").value.strip(),
		'challenge_title': Element("challenge_title").value.strip(),
		'uuid': str(uuid.uuid4()),
		'challenge_description': Element("challenge_description").value.strip(),
		'tags': tags,
		'depends_on': depends_on,
		'flags': collect_flags(),
		'hints': collect_hints()
	}

	ret = toml.dumps(challenge_object)
	# print('successfully dumped')

	output = Element('tomlDiv')
	output.element.innerHTML = ret

	return ret