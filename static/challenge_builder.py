# this is meant to be run via pyscript as part of the challenge builder web app

import toml

# import js
import uuid
from pyscript import Element
from js import document

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
</div>
"""

hint_html_template = """
<div class="card card-body" id="hint_set_XXX">
	Hint: XXX
	<p>
		Hint Cost:<input type="text" class="form-control hint" name="hint_XXX_cost" id="hint_XXX_cost" placeholder="How much will a player have to pay to view this hint?">
		Hint text:<textarea class="form-control hint" name="hint_XXX_text" id="hint_XXX_text" rows="2" width="100%" placeholder="This is the actual hint you are providing..."></textarea>
	</p>
</div>
"""



def collect_flags():
	flags = list()
	#print('here')
	for i in range(1,num_flags):
		#print(i)
		title = Element(f'flag_{i}_title')
		value = Element(f'flag_{i}_value')
		flag = Element(f'flag_{i}_flag')
		#print('flag values', title.value, value.value, flag.value)
		if title.value == None or value.value == None or flag.value == None: 
			break
		tmp = {
			'flag_title': title.value.strip(),
			'flag_value': int(value.value.strip()),
			'flag_flag' : flag.value.strip()
		}
		flags.append(tmp)
		#print(flags)

	return flags	

def collect_hints():
	hints = list()
	for i in range(1,num_hints):
		#print(i)
		cost = Element(f'hint_{i}_cost')
		text = Element(f'hint_{i}_text')
		#print('hint values', cost.value, text.value)
		if cost.value == None or text.value == None :
			break
		tmp = {
			'hint_cost': int(cost.value.strip()),
			'hint_text': text.value.strip()
		}
		hints.append(tmp)
		#print(hints)

	return hints	



def add_flag():
	global num_flags
	# print(f'adding a flag, {num_flags} total' )
	
	this_flag_html = flag_html_template.replace("XXX", str(num_flags))
	# this_flag_div = document.createElement("div")
	
	flag_div = document.querySelector(f'#flag_div')
	existing_flag_divs = flag_div.innerHTML
	flag_div.innerHTML = existing_flag_divs + this_flag_html
	num_flags += 1
	
	

def add_hint():
	global num_hints
	# print(f'adding a hint, {num_hints} total' )
	
	this_hint_html = hint_html_template.replace("XXX", str(num_hints))
	# this_hint_div = document.createElement("div")
	
	hint_div = document.querySelector(f'#hint_div')
	existing_hint_divs = hint_div.innerHTML
	hint_div.innerHTML = existing_hint_divs + this_hint_html
	num_hints += 1

def build_challenge():

	challenge_object = {
		'author': Element("author").value.strip(),
		'title': Element("title").value.strip(),
		'uuid': str(uuid.uuid4()),
		'description': Element("description").value.strip(),
		'tags': Element('tags').value.replace(' ','').lower().split(','),
		'depends_on': Element('depends_on').value.replace(' ','').lower().split(','),
		'flags': collect_flags(),
		'hints': collect_hints()
	}

	ret = toml.dumps(challenge_object)

	output = Element('outputDiv')
	output.write(ret)

	return challenge_object