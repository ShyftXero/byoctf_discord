# byoctf_discord - Bring Your Own [Challenge || Capture] The Flag


<img style="display: block;-webkit-user-select: none;margin: auto;background-color: hsl(0, 0%, 90%);" src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExeWxqbmJicmF0bXgzaGwxajZwOW1jbWRucDE0eGF1Z3Q0cmRxYndiaSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/M9TrcWs9M52TEaorKr/giphy.webp">

## DEFCON 32 - BIC VILLAGE

Come see my presentation at the Blacks In Cyber Village at DEFCON! 

"BYOCTF" - Bring Your Own [Challenges||Capture] The Flag
Speaker: Eli Mcrae 
Day: Friday August 9, 2024
Time: 2:00 PM

https://www.blacksincyberconf.com/bic-village

## 2600 shoutout from DJ PFEIF of Hack The Planet DNB show

We got a ahoutout in a write up for 2600 magazine in the summer 2024 issue. 

https://djpfeif.com/drum-bass-pfeif-radio-show/

## TL;DR
A CTF framework that allows players to submit and complete challenges from other players. They are rewarded when players solve their challenges. 

People always want to help, but they can't play if they create challenges for us. this addresses that.

Discord provides the UI/UX for the game

I'm not a great developer so code is a hodge-podge, but 90% of the time it works 100% of the time.

The idea is good, I promise, but the code is questionable.

You can think of BYOCTF as kind of like a potluck. The host provides a central core dish for folks to eat and everyone else brings a little something extra to chew on. 

#### The core features of the framework are 
- inter-player transactions (in-game economy for facilitating real-world info exchange).  Players can trade points amongst themselves for favors, info, etc.
- "challenges" don't have value; "flags" do have value. A challenge is a set of one or more flags. 
- user-contributed challenges that reward the creator with a percentage of the value of the flag that was captured.
- toml-based challenge description for "challenges as code" so you can hopefully just import this into any other framework that supports the idea in the future. 

#### limitations or cons of the framework
- it doesn't host files... you have to use some other file storage and provide a link to it (webserver, Google Drive, Dropbox, etc.)
- it doesn't host any services. our implementation doesn't spin up a docker container or anything ( although we could do something like that) 
- cognitive overhead compared to other jeopardy-style frameworks like ctfd (we're here for the real ones...) 

People kept asking if fs2600 was going to host Shell On The Border again. My answer internally was 'not until the byoc framework is done.' Here we are... 

presentation -> https://byoctf.com/slides

***Online challenge CREATOR***
https://validator.byoctf.com/create

***Online challenge validator***
https://validator.byoctf.com


Watch how to create a challenge on YouTube

[<img src="https://i.ytimg.com/vi/h-BqeWsldj0/maxresdefault.jpg" width="50%">](https://www.youtube.com/watch?v=h-BqeWsldj0")



Watch the teaser video on YouTube

[<img src="https://i.ytimg.com/vi/_eD0DLc8fg4/maxresdefault.jpg" width="50%">](https://www.youtube.com/watch?v=_eD0DLc8fg4")

---

## Features
This implements several features that are unique to SOTB or match our event's aesthetic

- User contributed challenges meaning GMs/hosts can play too. 
  - Internally validated flags (if you trust us to not look at flags)
  - Externally validated flags (if you don't trust us to not look at flags)
    - We provide a flag validation server for you to host on your own infrastructure. 
  - Purchasable hints
  - Reward system for user contributed challenges.
    - Some percentage of flag value
  - TOML based challenge definition. 
    - Use TOML... it's much nicer. Check out the `example_challenge.toml` vs `example_challenge.json`
    - There's a converter for challenges that exist in either format.
      - `converter.py to_toml chall.json chall.toml`
  
- Flag oriented
  - Points are bound to flags (except for externally validated challenges)
  - One flag can belong to several challenges. 
    - Challenges can be composed by binding specific aspects(flags) of other challenges. 
    - Think of xbox achievements or goals; "Forensicator: solve 3 forensics flags." 
- Bonus flags 
  - flags not bound to a specific challenge. (internally they are)
  - These are for flags that can be "found" in the environment or created in an impromptu fashion. 
  - Throw-away flags (look under your chair type of thing)
- Inter-player transactions via the "tip" system.
  - informal hint purchases from other players
  - provides a mechanism for players to try and social engineer points off eachother.
  - rewards for kindness
- Team oriented
  - scores are often displayed in the context of your team.
  - hints purchased by a teammate are viewable by all teammates
  - submissions and unlocked challenges are viewable by all teammates. 
  - if you buy it, your team gets access to it.
  - You can't submit flags authored by your team, of course. 
  - Configurable team size; defaults to 4
- Public/Private mode for the scoreboard. 
  - you can see your team scores but not other teams. 
  - helps motivate teams who would give up if they felt they didn't stand a chance.
  - Can show MVPs for individual score. 
- Challenge dependencies
  - Challenges are hidden until all flags from each "parent" challenge (or dependecy) is solved. 
  - _pretty sure this is working as intended._ 
  - BYOC challenges can depend on byoc or non-byoc challenges. 
    - Allows individuals to extend a challenge that already exists if they are inspired to do so. 
- Reactive points for solves
  - FirstBlood
    - Bonus for first team to solve a flag
    - default
  - Flag Decay
    - Flags become less valuable as they are solved by other teams.
    - not default, fully implemented, or tested.
  - Configurable via text editor or CLI
    - decay rate
    - BYOC fees and reward 
    - firstblood rewards
    - see `settings.py` and `ctrl_ctf.py`
- Rating system for challenges. 
  - You can only rate a challenge if you or your team have captured at least one flag from it. 
- User management and registration handled via discord...
  - Uses account name and its descriminator e.g. `shyft#0760`
- Flag submission is ratelimited
  - tunable via settings. 
- Most commands are restricted to DM with the bot
  - prevents flag, score, or sensitive info leak in public channels. 
  - `!tip` is allowed in public channels to inform others that you offered up a tip. This allows you to use `@<discord_name>` if they are in the same channel. (`statewide hackery` or a dedicated CTF channel is a good place for that)
  - It can be done in the DM as well but you need the username of the recipient (like `shyft#0760`; click on their name in Discord to view that.)

## Expected Features
- ~~BYOC challenges being dependent on other BYOC challenges or Non BYOC challenges.~~ 
  - This seems to be working now.
- public http scoreboard for live events. 
- API access to challenges and solves. (removing dependecy on discord although it is integral right now; not any time soon)
- maybe an admin web gui? idk... 

## TODO / bugs
- Flag solves only report 1 challenge that it is a part of during the "congrats" message. 
- ~~You can submit a flag for a challenge that isn't unlocked yet.~~ 
  - ~~may not be a huge issue. How would you know to find it if you hadn't been prompted to search for it some how?~~
  - ~~this is more likely to occur for challenges with a lot of narrative and that build on each other.~~
    - ~~things where you are likely to have to "investigate" for perform some sort of forensics as part of a later challenge.~~
  - resolved. 100% unlock
- We chose to not show your teammates challenges or your own challenges because you could not solve them anyway. 
  - You can use `!bstat` to see your challenges. 
  - This helps prevent a teammate working on your challenges when they couldn't submit it anyway. 
---
## How to play

Key commands 
- `!reg <team_name> <team_password>` - register and join *teamname*; super case-sensitive.  
  -- wrap in quotes if you have spaces in the teamname; 
  -- if the team exists and your password is correct, you're in. 
  -- if no team exists with the name specified, the team will be created with password specified. 
  -- leading and trailing spaces are stripped from team name and password.
- `!top` - shows your score 
- `!all [tag]` - filter challenges by tag; use !tag to exclude; `!byoc` to only view "official" challenges 
- `!v <challenge_id>` - detail view of a specific challenge
- `!sub <flag>` - submit a flag you find while working on a challenge
- `!esub <chall_id> <flag>` - submit an externally validated flag. (challenge should say if it's externally validated.)
- `!solves` - show all the flags your team has submitted. 
- `!unsolved` - show all of the unlocked challenges that don't have at least one submission. 
- `!rate <challenge_id> <val>` - rate a challenge on a scale (default 1-5). if others say it's garbage, don't waste your time... you can only rate if you capture at least one of the flags for the challenge. 
- `!log` - all transactions you participated in (sender or recipient of a tip, BYOC rewards and fees, and solves among other things)
- `!pub` - all transactions that have happened in the game. if scoreboard is private, amounts are omitted. 
- `!psol [challenge_id]` - all solves for all challenges or just challenge_id 
- `!help` - shows the long name of all of the commands. Most of the above commands are aliases or shorthand for a longer command.

---

# BYOC Challenges
## Common criticisms of the BYOC concept and why it sucks 
- ***Creating an impossible challenge in an effort distract players.*** 
  - This is a possibility and always has been.
  - Part of developing your CTF skillset is to be able to recognize this and manage your time effectively. 
  - There is also the fact that it costs points to post a challenge. that might be enough of a deterent for most. Others, maybe not. 
  - I don't think the issue will be rampant enough to warrant scrapping the idea.
- ***Creating a trivial challenge worth a lot of points***
  - I believe that this issue will self-regulate. 
  - If it's just a simple challenge and everyone can solve it, then it doesn't have much bearing on the final outcome as everyone can/will solve it.
  - As mentioned we can cap/stop the rewards for a challenge or disable it altogether. We can also take points away for bad behavior. 
  - If everyone's a loser, no one's a loser. 
  - There's also a task management component to this. Don't let one of the high value easy flags slip by. 
- ***Otherwise legitimate but over or under-valued challenges***
  - This is the hardest one to address.
  - Remember, GM's have access to tools and can adjust the base value of a flag to bring them in line. 
    - don't rely on this. existing solves won't account for the new flag's value.   
    - see the next section. -> `Notes or guidance for developing challenges.`
- If you don't want to risk it and avoid BYOC, use `!all !byoc` 
  - `!` like _not_ or a logical inversion.
- ***Cheating in the game***
  - The highest form of cheating is preventing others from being able to play, compete, and/or have fun.
  - Don't do this.
  - In my opinion, the following examples are "cheating" in various degrees of severity.  Hurting computers is mostly ok. Hurting people is not. 
    - intentional denial of service to shared infrastructure (specific challenge or game infrastructure like scoreboard or flag submission) (highest infraction)
    - theft of credentials by social engineering and draining those accounts. (greater infraction)
    - abusing the game infrastructure and boosting or draining accounts. (lesser infraction) 
    - leaking all flags from the scoreboard somehow or granting infinite points (least infraction; if unabused might be rewarded)
- ***Challenge Cloning***
  - A player copies the text of someone else's challenge and posts it as their own.
  - clever attempt at social engineering other players into submitting flags to you instead of the scoreboard somehow.
  - In order to submit a challenge, you have to submit the flag (except externally validated flags)
  - the mitigation for this is that you have to stake 50% of the total challenge value (sum of all flags) in order to have the challenge show up for other players.
  - While it's a viable attack strat, it's a gamble because you might not get any solves.
  - say you target a 100-point (say a zipfile cracking challenge) and clone it by posting it for 1000 to entice others to attempt it.
    - you'd have to submit it as an externally validated flag to bypass the checks for flag uniqueness
    - you'd have to pay the 50% posting fee (500 points in this case) to submit and post the flag for others.
    - you'd have to get others to solve, observe the proxied results, then submit them hoping they're correct.
    - when you get a solve you get a 25% return (250 points )
    - you need two solves to get your money back + the 100 you submitted for the original flag.
    - you'd get 250 points per solve; People who solve your chall get 1000 points
    - you are limited by the number of teams (only one player per team can get points from a solve)
  - In addition to the limited submissions you can disable the challenge and undo the transactions if the game is abused in this way.
    - I think this is the best way.
    - this would require you being made aware of the issue.
    - you can delete all solves and transactions related to the problematic challenge.
  - it doesn't exist but I could implement a command that purges all the solves and transactions related to a problematic challenge. [TODO]
  - if you tell people about the attack path, it will seem less cool and they might not go down that path. (I'm an optimist at heart)
---
## A few notes about creating BYOC challenges
- ### ***There is no way to edit your challenge once you commit it***
  - Make sure you don't have typos 
  - use DNS names rather than hardcoded IPs for links
  - use non-dynamic links for sharing files (google drive may yield a different link even you create a new version of the "same" file )
  - use a git repo?
  - ***Make sure it's solvable*** 
    - The bot can't prove or know that it is or isn't
  - ***ALL SALES ARE FINAL!***
    - If it's not solvable, that is on you. you lost the points it cost to post it. 
- Cumulative challenge value is the sum of flag values
  - Must exceed 100 points ; configurable
- Challenge titles must be unique. 
- Flags must be globally unique.   
  - potential info leak about a flag that exists, but we just have to accept that risk... `!byoc_check` and `!byoc_commit` rate limited to help mitigate this.
- Description is limited to 1500 chars. (more of a discord UI thing. messages can't exceed 2000 chars, )
- Hints are given to user by lowest cost first. 
  - create the hint you would like to give first with the lowest cost.
  - points are required to purchase hints. (doesn't reduce value of challenge.) 
    - Admins can grant points via ctrl_ctf.py but shouldn't make a habit of it...
  - ~~***Question to the audience: Should authors get a portion of hint buys?***~~
    - Went ahead and implemented it. You can tune the reward rate in settings.py or via cmdline.  
- The framework doesn't (can't) host files. 
  - Link to a pastebin, google drive, github, torrent, etc. if you need storage or more space for words... 
  - Files - most are ephimeral and are deleted after 1-2 weeks
    - https://transfer.sh/ or http://jxm5d6emw5rknovg.onion/
      - 10gb files; no account; wget-able; tor service for your protection or whatever.
    - https://bashupload.com/
    - https://www.file.io/
    - https://onionshare.org/ - a good choice but requires tooling.
    - https://github.com - not ephimeral
      - **least sketch and editable by you if you make a mistake. **
      - 100mb file limit
      - maybe serve large file via transfer.sh and update the link every couple of weeks(if the event runs that long)?
  - Words
    - https://gist.github.com/
    - https://pastebin.com/
- Infrastructure
  - if you are making complex challenges, consider the "solvability" if one team trashes the server and prevents other teams from submitting your flag. 
  - team isolation or at least multiple instances are helpful to mitigate this. 
  - How will teams access your hosted challenges if they aren't on the same network?
  - These services will allow you to host stuff on a private network but all of them have their tradeoffs between cost (to you) or complexity (for players)
    - **TOR**
    - **Zerotier**
    - netbird
    - weron
    - nebula
    
- By default, it costs 50% of the total challenge value (sum of flags) to post a challenge. 
- By default, your reward for the solve of a flag which is part of your challenge is 25% of that flags value. 
  - If the challenge is externally validated, it's based on the challenge value.
  - You will get a reward of 25% of the flag value everytime there is a successful solve. (not including firstblood or decayed point value)
  - Example: (assuming default settings for fees and rewards)
```
- you have a challenge with 2 flags.
  - flag 1 is worth 150 points and flag 2 is 50 points for a total of 200 points
- It will cost you 100 points to post it via `!byoc_commit` so you do.
- Now you are down `100` points
- When the first solve comes in for flag 1, you will get a reward of `37.5` points
- Now you are only down `62.5` points. 
- When the second solve for flag 1 comes in, you will get another reward of `37.5` points
- Now you are only down `25` points.
- When the first solve comes in for flag 2, you will get a reward of `12.5` points
- Now you are only down `12.5` points.
- When the third solve for flag 1 solve for flag 1 comes in, you will get another reward of `37.5` points
- At this point you have earned back your commit fee and have turned a profit of `25` points
```
  - This is only possible if your challenge is solvable. You could create some time-sink challenge that's impossible, but you'd have to pay to do so... 
  - Also, keep in mind that the BYOC fee and rewards can be tuned while the game is running. All transactions that take place after the change will reflect the newer rate and old transactions will reflect the older rate.
  - ~~**Consider adding a rating system for BYOC challs**~~ 
    - Implemented this. scale is tunable. default is 1-5. use `!rate <chall_id> <1-5>`
  - Admins can also prevent your challenge from being solvable if you figure out a scheme that is in violation of the spirit of the game. That depends on them and you, of course. 
- ~~This sucks to admit... but we can still find your externally validated flags if someone successfully submits it... it'll end up in the Solves table in the db (we won't know the flag before that happens though)~~
  - ~~we need to store it the flag so the `!solves` command can show you which flags you've already submitted.~~ 
  - ~~open to arguments against this or a PR to avoid it.~~ 
  - We kind of worked around this by storing a hash of the flag in the solve text rather than the flag itself. As the author you will see the hash in the solve and can hash your own flags to see which one matches. 
  - Keep in mind that we still touch the unhashed flag from a legitimate solve so you have to trust that we're not logging... 😉 good luck... 
---
## Notes or guidance for developing challenges.
Most of the following are considerations regarding building your challenge. 
- ***Defining outcomes/objectives***
  - How much prior knowledge do you have to have in order to accomplish the task? 
    - Can you learn all of it during the amount of time that the challenge is available
  - Is this something targeting a beginner in infosec or a beginner in a certian infosec discipline
    - computer n00b vs web app pentesting n00b but 10 year network engineering vet vs ...
  - Are you validating experience or guiding a learning experience?
- ***Assigning a score to your challenge***
  - What is the range or scale of your event?
    - many are done in 25-50 point increments upto 500
    - This is arbitrary. 
  - how "off the shelf" is the attack/vector?
    - does a metasploit module already exist?
  - How "custom" is the target system or attack technique?
    - stock config = less understanding of the application required to exploit
    - intentionally misconfigured = more understanding of the application required to exploit
    - how recent is the application, exploit, or technique?
    - 
  - What skills are required to accomplish the challenge?
    - how much customization/tailoring of existing exploit code is required?
    - How much code
  - How impactful is the challenge?
    - "gee whiz" factor for the uninitated
  - How much attention do you want your challenge to get?
    - It's just a reality that high value flags get looked at more.
  - ? 
- ***What infrastructure do I(the author of the challenge) need to have in place?***
  - This doesn't/shouldn't have much bearing on the score. 
  - **REALLY** depends on the challenge
    - You should have one server per team if:
      - attempting to solve the challenge (attacking/exploiting the server) has a high probability of reducing other teams ability to solve.
        - this is like having someone reset your box on hackthebox just after you get a shell. (realistic-ish but frustrating) 
    - You could use a shared server if:
      - if attacking the server has a low probability of reducing other teams ability to solve.
      - the server is simply hosting files for download.  
  - Docker is a fair middle-ground regarding hosting a suite of challenges on a single server while minimizing exposure/risk of compromising other challenges if exploited. 
    - We have some dockerfiles and control scripts to talk about that if the time comes. 
  - The external validation server (or one like it) if you choose to not share your flags with the bot.
- ***what infrastructure will the players need to solve your challenge?***
  - I would try to avoid "pay to win" challenges. ex: Being able to buy more GPU instances for a password cracking challenge. Don't price people out.  
  - Does a required SaaS have a free tier? 
  - Do solvers need a publicly routable IP to solve? 
  - Do they need some sort of VPN? see section above `A few notes about BYOC challenges`
 
---

# Setup

See [SETUP.md](SETUP.md)
  
---
## Submitting a challenge 
- Validate your challenge by attaching the toml file in a DM to the bot with the command `!byoc_check`
  - If it's valid, an extended preview will show up showing the cost. 
- Commit your challenge (actually post it) by attaching the toml file in a DM to the bot with the command `!byoc_commit`
  - If the challenge is valid, the preview will show up and you will be prompted to type `confirm` within 10 seconds.
    - If you do, you are charged the fee (again, by default 50% of the cumulative value) and the challenge is made available to others.
- Others can use `!all byoc` and `!v <chall_id>` to see it. 
  
---
A basic single flag challenge in toml
```toml
author = "Combaticus#8292"
challenge_title = "r3d's challenge"
challenge_description = "good luck finding my flag at validator.byoctf.com"
uuid = "1f495409-a84b-43a2-bf8e-90fd979024f4" # a uuid4 string
tags = [ "pentest",]
[[flags]]
flag_title = "r3d flag"
flag_value = 200
flag_flag = "FLAG{this_is_a_flag_from_r3d}"

[[hints]]
hint_cost = 10
hint_text = "the flag is easy"
```
A multi-flag challenge in TOML
```toml
author = "Combaticus#8292"
challenge_title = "r3d's multi-flag challenge"
challenge_description = "good luck finding my flags at 3.43.54.28"
tags = [ "pentest", "forensics",]
uuid = "e66622ea-ac8e-4bcd-a873-a485f4a3724b"
[[flags]]
flag_title = "flag 1 "
flag_value = 100
flag_flag = "FLAG{this_is_flag_1_for_multiflag}"

[[flags]]
flag_title = "flag 2"
flag_value = 300
flag_flag = "FLAG{this_is_flag_2_for_multiflag}"

[[hints]]
hint_cost = 25
hint_text = "Both of the the flags are easy"
```

A challenge that depends on other challenges (by challenge ID) in TOML
```toml
author = "Combaticus#8292"
challenge_title = "r3d's child challenge"
challenge_description = "good luck finding my flag"
tags = [ "pentest",]
depends_on = [ 6, 7,] # these are uuid strings now...
[[flags]]
flag_title = "r3d dependent flag "
flag_value = 200
flag_flag = "FLAG{solved_6_7}"

[[hints]]
hint_cost = 10
hint_text = "the flag depends on solving chall 6 and 7"
```

An externally validated challenge in TOML.
```toml
author = "Combaticus#8292"
challenge_title = "r3d's externally validated challenge"
challenge_description = "good luck finding my flag. At http://1.2.3.4/hackme "
uuid='2e9e73a9-3e02-4db9-871e-fe5ffde1deb0'
tags = [ "coding",]
external_challenge_value = 250
external_validation = true
external_validation_url = "http://localhost:5000/validate"
# If you don't trust us to not look at the flags you submit, you can host a validation server on some public server and the bot can validate against that.
# I'd use a domain rather than IP because there's no public mechanism to update challenges... These are limited to one flag per challenge. sorry... It will send a post to your endpoint similar to {'challenge_id':<some_id>, 'flag':<some_flag>} . It will expect a response of {'flag':'correct'} or {'flag':'incorrect'} a basic implementation of that functionality will be provided.
# YOU WILL HAVE TO MENTION IN THE CHALLENGE WHETHER OR NOT THIS IS AN EXTERNALLY VALIDATED CHALLENGE.
# There's a different command to validate those flags. !byoc_ext <chall_id> <flag>; we use the validation url (must end in /validate with no trailing slash).
# feel free to extend the server we provide... You can host all of the flags for all of your challenges in the single flags.json file.
# you won't know a challenge ID to serve as the key until you commit your challenge. Currently, there is no first blood reward for externally validated challenges.

[[hints]]
hint_cost = 25
hint_text = "the flag is also easy"


```

- Clone the server code -> https://github.com/ShyftXero/byoctf_ext_validation
- Start the external validation server prior to checking your challenge. part of the check is to see if it's able to validate. 
- You won't know your challenge ID to update the `flags.json` on your validation server until you actually commit your challenge and pay the fee. 
  - just use a text editor. and up date the key that corresponds to the flag. 
  - you only need one server to validate multiple challenges. 


There are a couple of other examples in the `example_challenges` folder... 




# other cool stuff

https://github.com/tamuctf/ctfd-portable-challenges-plugin
---
# Info that may be redundant... 
This was built with Shell On The Border in mind so it may not be suitable for any other events. 

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

~~No limit on team size.~~ Configurable; defaults to 4

So, for the paranoid, you don't have to trust us with the flags. Although, this does make it harder to have a unified experience and violates the 'flag oriented' design, but... whatever. 

we provide a basic server for you to host somewhere publicly accessible. When someone tries to submit a flag, we forward the request to your server and you confirm whether it was correct or incorrect. 

You're limited on what you can do in this mode. One flag per challenge. 

This is nice because it allows the GMs to be able to compete as well. 

You just have to trust that we aren't capturing all of the requests that we forward to you for validation... we aren't... 


that's all the documentation for now... 
