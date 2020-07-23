# byoctf_discord - Bring Your Own [Challenge || Capture] The Flag

## TL;DR
A CTF framework that allows players to submit and complete challenges from other players. They are rewarded when players solve their challenges. 

People always want to help, but they can't play if they create challenges for us. this addresses that.

Discord provides the UI/UX 

Users can trade points amongst themselves for favors, info, etc.

I'm not a great dev so code is a hodge-podge, but it *mostly* works.

People kept asking if fs2600 was going to host Shell On The Border again. My answer internally was 'not until the byoc framework is done.' Here we are... 

---

## Features
This implements several features that are unique to SOTB or match our event's aesthetique

- User contributed challenges meaning GMs/hosts can play too. 
  - Internally validated flags (if you trust us to not look at flags)
  - Externally validated flags (if you don't trust us to not look at flags)
    - We provide a demo server for you to host on your own infrastructure. 
  - Purchasable hints
  - Reward system for user contributed challenges.
    - Some percentage of flag value
  - JSON based challenge definition.
- Flag oriented
  - Points are bound to flags (except for externally validated challenges)
- Bonus flags 
  - flags not bound to a specific challenge
  - useful for flags "found" in the environment or created in an impromptu fashion
- Inter-player transactions via the "tip" system.
  - informal hint purchases? 
  - drug transactions?
  - provides a mechanism for players to try and social engineer points off eachother.
  - rewards for kindness?
- Team oriented
  - scores are often displayed in the context of your team.
  - hints purchased by a teammate are viewable by all teammates
  - submissions and unlocked challenges are viewable by all teammates. 
  - if you buy it, your team gets access to it.
  - You can't submit flags authored by your team, of course. 
- Public/Private mode for the scoreboard. 
  - you can see your team scores but not other teams. 
  - helps motivate teams who would give up if they felt they didn't stand a chance.
  - Can show MVPs for individual score. 
- FirstBlood
  - Bonus for first solve of a flag
- Flag Decay
  - Flags become less valuable as they are solved by other teams.
- Configurable via text editor or CLI
  - decay rate
  - BYOC fees and reward 
  - firstblood rewards
  - see `settings.py` and `ctrl_ctf.py`
- User management and registration handled via discord...
  - uses account name and its descriminator e.g. `shyft#0760`
- Flag submission is ratelimited
  - tunable via settings. 
- Most commands are restricted to DM with the bot
  - prevents flag and score info leak in public channels. 
  - `!tip` is allowed in public channels to inform others that you offered up a tip. This allows you to use `@<discord_name>` if they are in the same channel. (`statewide hackery` or a dedicated CTF channel is a good place for that)
  - It can be done in the DM as well but you need the username of the recipient (like `shyft#0760`; click on their name in Discord to view that.)
---
## How to play

Key commands 
- `!reg <team_name> <team_password>` - register and join *teamname*; super case-sensitive.  
  - wrap in quotes if you have spaces in the teamname; 
  - if the team exists and your password is correct, you're in. 
  - if no team exists with the name specified, the team will be created with password specified. 
  - leading and trailing spaces are stripped from team name and password.
- `!top` - shows your score 
- `!all` - list all challenges
- `!v <challenge_id>` - detail view of a specific challenge
- `!sub <flag>` - submit a flag you find while working on a challenge
- `!esub <chall_id> <flag>` - submit an externally validated flag. (challenge should say if it's externally validated.)
- `!solves` - show all the flags your team has submitted. 
- `!log` - all transactions you particpated in (sender or recipient of a tip, BYOC rewards and fees, and solves among other things)
- `!help` - shows the long name of all of the commands. Most of the above commands are aliases or shorthand for a longer command. 
---

## BYOC Challenges

Notes about BYOC challenges
- ### ***There is no way to edit your challenge once you commit it***
  - Make sure you don't have typos 
  - use DNS names rather than hardcoded IPs for links
  - use non-dynamic links for sharing files (google drive may yield a different link even you create a new version of the "same" file )
  - ***Make sure it's solvable*** 
    - The bot can't prove or know that it is or isn't
  - ***ALL SALES ARE FINAL!***
- Cumulative challenge value is the sum of flag values
  - Must exceed 100 points
- Challenge titles must be unique. 
- Flags must be globally unique.   
  - potential info leak about a flag that exists, but we just have to accept that... 
- Description is limited to 1500 chars. 
- The framework doesn't (can't) host files. 
  - Link to a pastebin, google drive, mega, torrent, etc. if you need storage or more space for words... 
- By default, it costs 50% of the total challenge value to post a challenge. 
- By default, your reward for the solve of a flag which is part of your challenge is 25% of that flags value. 
  - if the challenge is externally validated, it's based on the challenge value. 
- *This sucks to admit... but we can still find your externally validated flags if someone successfully submits it... it'll end up in the Solves table in the db (we won't know the flag before that happens though)*
  - we need to store it the flag so the `!solves` command can show you which flags you've already submitted. 
  - open to arguments against this. 

## Submitting a challenge
- Validate your challenge by attaching the json file in a DM to the bot with the command `!byoc_check`
  - If it's valid, an extended preview will show up showing the cost. 
- Commit your challenge (actually post it) by attaching the json file in a DM to the bot with the command `!byoc_commit`
  - If the challenge is valid, the preview will show up and you will be prompted to type `confirm` within 10 seconds.
    - If you do, you are charged the fee (again, by default 50% of the cumulative value) and the challenge is made available to others.
- Others can use `!v <chall_id>` to see it. 
  
---
A basic single flag challenge.
```json
{
    "author": "Combaticus#8292",
    "challenge_title": "r3d's challenge",
    "challenge_description": "good luck finding my flag",
    "tags": ["pentest"], 
    "flags": [
        {
            "flag_title": "r3d flag", 
            "flag_value": 200,
            "flag_flag": "FLAG{this_is_a_flag_from_r3d}"

        }
    ], 
    "hints": [
        {
            "hint_cost": 10,
            "hint_text": "the flag is easy"
        }
    ]
}
```
A challenge with multiple flags.
```json
{
    "author": "Combaticus#8292",
    "challenge_title": "r3d's multi-flag challenge",
    "challenge_description": "good luck finding my flags",
    "tags": ["pentest", "forensics"], 
    "flags": [
        {
            "flag_title": "flag 1 ", 
            "flag_value": 100,
            "flag_flag": "FLAG{this_is_flag_1_for_multiflag}"

        },
        {
            "flag_title": "flag 2", 
            "flag_value": 300,
            "flag_flag": "FLAG{this_is_flag_2_for_multiflag}"

        }
    ], 
    "hints": [
        {
            "hint_cost": 25,
            "hint_text": "Both of the the flags are easy"
        }
    ]
}
```
An externally validated challenge.
```json
{
    "author": "Combaticus#8292",
    "challenge_title": "r3d's external challenge",
    "challenge_description": "good luck finding my flag. ",
    "tags": ["coding"], 
    "hints": [
        {
            "hint_cost": 25,
            "hint_text": "the flag is also easy"
        }
    ],
    "external_challenge_value": 250, 
    "external_validation": true, 
    "external_validation_url": "http://mydomain.com:5000/validate"
}
```
- Start the external validation server prior to checking your challenge. part of the check is to see if it's able to validate. 
- You won't know your challenge ID to update the `flags.json` on your validation server until you actually commit your challenge and pay the fee. 
  - just use a text editor. and up date the key that corresponds to the flag. 
  - you only need one server to validate multiple challenges. 


There are a couple of other examples in the `example_challenges` folder... 


---

# Setup

add your own token to `secrets.py`

```bash
git clone https://github.com/ShyftXero/byoctf_discord
cd byoctf_discord
echo "DISCORD_TOKEN='asdfasdfasdf'" > secrets.py # https://discord.com/developers/applications; setup a bot  
./ctrl_ctf.py FULL_RESET # creates the db and fills with test data by calling populateTestData.py
python byoctf_discord.py
```

## Info that may be redundant... 
Whoa... this was harder to do that I thought it would be... but CTFs are fun and so is running them.

lot's of edge cases to consider for you pesky hackers...


I wanted to build this for the next iteration of SOTB or any CTF that fs2600 crew participates in running. 

This incarnation lives in the Arkansas Hackers discord server as a bot. 

It's meant to be interacted with primarily via DM, but there are a couple of reasons to interact with it in a public channel. 

One of the designs goals that I thought would be interesting was the concept of being able to trade points between users. 

We have other odd-ball games like 0x21 at SOTB and we wanted a shady grey market of info trading to be created. 

We want points to approximate a 'currency' during the CTF. You can send a `tip` to so someone for helping you or to settle some debt.  

I wanted the framework to be "flag oriented" rather than "challenge oriented". Points are associated with a flag rather than the challenge itself. 

A challenge's value is the sum of the values of its flags. this gives us partial completion. 

Also a single flag can exist as part of multiple challenges. This allows for interesting interweaving of challenges (for the GMs; not the BYOC players yet...)

One of the key features (and main reason for building this) is the ability to allow users to partcipate in the fun of creating challenges. 

They describe their challenge in a json file and send it to the automaton.

The bot doesn't/can't host any files so that is on the challenge author to figure out. The description is also limited to 1500 chars. Link to a pastebin, google drive, mega, torrent, etc. if you need storage or more space for words... 

Users have to pay a percentage of the value of their challenge before it becomes available to other players. 

This is to provide *some* incentive for it to be solvable by others (not a guarantee). 

They are given a reward for every team that solves it. this can become a money maker for a team. 

For example, player1 a challenge worth 500 points costs 250 points to post. (50% of value; this is tunable) 

player2 can submit the flag for the 500 points (and possible firstblood bonus of 10% for 550 points; again tunable) 

player1 will receive a reward of 25% (125 points; also tunable).

Two separate teams will have to submit the flag in order for player1 to break even. 

They will profit on the third solve. 

Obviously, teammates can't solve your flags. 

This framework is very team oriented.

No limit on team size. 

So, for the paranoid, you don't have to trust us with the flags. Although, this does make it harder to have a unified experience and violates the 'flag oriented' design, but... whatever. 

we provide a basic server for you to host somewhere publicly accessible. When someone tries to submit a flag, we forward the request to your server and you confirm whether it was correct or incorrect. 

You're limited on what you can do in this mode. One flag per challenge. 

This is nice because it allows the GMs to be able to compete as well. 

You just have to trust that we aren't capturing all of the requests that we forward to you for validation... we aren't... 


that's all the documentation for now... 