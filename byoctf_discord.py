import os
import random
import datetime
import json
from typing import Union

from loguru import logger
logger.add('byoctf.log')

import requests
from terminaltables import AsciiTable
import discord
from discord.ext import commands

from secrets import DISCORD_TOKEN
import database as db


import json

from settings import SETTINGS, init_config, is_initialized

if is_initialized() == False: # basically the ./byoctf_diskcache/cache.db has data in it. rm to reset
    init_config()



bot = commands.Bot(command_prefix='!')

def username(obj):
    if hasattr(obj, "author"): 
        return f'{obj.author.name}#{obj.author.discriminator}'
    elif type(obj) == discord.User or type(obj) == discord.user.ClientUser:
        return f'{obj.name}#{obj.discriminator}'
    
    return "__NONE__"

async def getDiscordUser(ctx, target_user):
    # this is only for the gui representation of the recipient
    # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.UserConverter
    uc = discord.ext.commands.UserConverter()
    res =  await uc.convert(ctx, target_user)
    return res

def renderChallenge(result, preview=False):
    """returns the string to be sent to the user via discord. preview is mostly for BYOC challenges to validate that flags came through correctly.""" 
    msg = ""
    if preview == True:
        msg = f"Challenge valid. \nHere's a preview:\n"
        msg += f"It will cost `{result['cost']}` points to post with `!byoc_commit`\n"
    
    msg += '-'*40 + '\n'
    msg += f"Title: `{result['challenge_title']}`\n"
    msg += f"Value: `{result['value']}` points\n"
    msg += f"Description: {result['challenge_description']}\n"
    msg += '-'*40 + '\n'
    
    if preview == True:
        msg += "Flags:\n"
        for flag in result['flags']:
            msg += f"flag: `{flag['flag_flag']}` value: `{flag['flag_value']}` title: `{flag['flag_title']}`\n" 
    return msg

@bot.event
async def on_ready():
    logger.debug(f'{bot.user.name} is online and awaiting your command!')

@db.db_session()
@bot.command(name='register', help='register on the scoreboard. !register <teamname>; wrap team name in quotes if you need a space')
async def register(ctx, teamname=None):
    if SETTINGS['registration'] == 'disabled':
        await ctx.send("registration is disabled")
        return

    if teamname == None:
        await ctx.send("I know it looks like teamname is an optional parameter, but it's not... sorry. ")
        return
   

    with db.db_session:
        team = list(db.select(t for t in db.Team if t.name == teamname))

        user = list(db.select(u for u in db.User if username(ctx) == u.name)) #returns True or False if 
        if len(user) > 0:
            msg = f'already registered as `{username(ctx)}` on team `{user[0].team.name}`'
            await ctx.send(msg)
            return
        
        
        
        if len(team) == 0:
            team = db.Team(name=teamname)
            user = db.User(name=username(ctx), team=team) # team didn't exist
        else:
            user = db.User(name=username(ctx), team=team[0]) # team already existed
        
        db.commit()
        msg = f'Registered as `{username(ctx)}` on team `{teamname}`'
        logger.debug(msg)
        await ctx.send(msg)



@bot.command(name='status', help="shows status information about the CTF")
async def status(ctx):

    data = [(k,SETTINGS[k]) for k in SETTINGS.iterkeys() if k[0] != '_'] # filter out the private settings; see settings.py config object
    data.insert(0, ['Setting','Value'])
    table = AsciiTable(data)
    await ctx.send(f'CTF Status ```{table.table}```')


@bot.command(name='scores', help='shows your indivivually earned points, your teams collective points, and the top N teams without their scores.', aliases=['score','points','top'])
async def scores(ctx):
    # individual score
    msg = ''
    with db.db_session:
        user = db.select(user for user in db.User if username(ctx) == user.name).first()
        # logger.debug(f'{user}, {type(user)}, {dir(user)}')
        
        
        individual_points = db.getScore(user)
        logger.debug(f'individual points {individual_points}')
        
        # teammates scores
        teammates = db.getTeammateScores(user)
        teammates.insert(0, ['Teammate', 'Score'])
        table = AsciiTable(teammates)
        
        # teammates.pop(0) # remove the table header
        team_points = sum([v for k,v in teammates[1:]]) #skip header

        msg += f'Your score is `{individual_points}`\n'
        msg += f'\nTeam `{user.team.name}` has `{team_points}` ```{table.table}```'
        
        # await ctx.send(msg)


        if SETTINGS['scoreboard'] == 'public':
            #top 3 team scores
            scores = db.getTopTeams(num=SETTINGS['_scoreboard_size']) # private settings with _
            scores.insert(0, ['Team Name', 'Score'])
            table = AsciiTable(scores)
            
            msg += f'Top {SETTINGS["_scoreboard_size"]} Team scores \n```{table.table}```'

        if SETTINGS['_show_mvp'] == True:
            # top players in the game
            topPlayers = db.topPlayers(num=SETTINGS['_mvp_size'])
            data = [(p.name, p.team.name, v) for p,v in topPlayers]
            data.insert(0, ['Player', 'Team', 'Score'])
            table = AsciiTable(data)
            msg += f'Top {SETTINGS["_mvp_size"]} Players\n```{table.table}```'

        await ctx.send(msg)



@bot.command(name='submit', help='submit a flag e.g. !submit FLAG{TESTFLAG}', aliases=['sub'])
# @bot.command()
# @commands.has_role("CTF_player")
async def submit(ctx, submitted_flag: str = None):

    if submitted_flag == 'FLAG{TESTFLAG}':
        ctx.send("You have submitted the test flag successfuly...")
        return 

    logger.debug(f"{username(ctx)} is attempting to submit '{submitted_flag}'")
    
    with db.db_session:
        # is this a valid flag
        res = list(db.select(flag for flag in db.Flag if submitted_flag == flag.flag))
        # logger.debug('res', type(res), len(res), res)

        if len(res) == 0:
            msg = f'incorrect: we got "{submitted_flag}"'
            logger.debug(msg)
            await ctx.send(msg)
            return

        user = db.User.get(name=username(ctx))
        flag = res[0]

        # have I already submitted this flag?
        solves = list(db.select(solve for solve in db.Solve if submitted_flag == solve.flag.flag and username(ctx) == solve.user.name)) # should be an empty list 

        if len(solves) > 0: 
            msg = f"You've already submitted `{submitted_flag}` at {solves[0].time} "
            logger.debug(msg)
            await ctx.send(msg)
            return

        # has a teammate submitted this flag? 

        teammates = db.getTeammates(user)
        solved = []
        for teammate in teammates:
            res = list(db.select(solve for solve in db.Solve if submitted_flag == solve.flag.flag and teammate.name == solve.user.name))

            # logger.debug('res = ', res)
            if len(res) > 0: # already submitted by a teammate 
                msg = f"{res[0].user.name} already submitted `{submitted_flag}` at {res[0].time} "
                logger.debug(msg)
                await ctx.send(msg)
                return
        
        # did this user author the flag?
        if flag.author.name == user.name:
            await ctx.send("You can't submit a flag from your own challenges...")
            return 
        # did someone else on their team author this flag? 
        for teammate in teammates:
            if flag.author.name == teammate.name :
                await ctx.send("You can't submit a flag created by someone on your own team...")
                return 


         # if I get this far, it has not been solved by any of my team

        msg = "Correct!\n"

        challenge = db.select(c for c in db.Challenge if flag in c.flags).first()
        
        if challenge:     # was this flag part of a challenge? 
            # logger.debug("challenge: ", challenge, type(challenge), dir(challenge))
            msg += f'You submitted a flag for challenge `{challenge.title}`.\n'
        
        
        reward = flag.value 
        if flag.unsolved == True:
            
            reward += flag.value * .1
            flag.unsolved = False
            msg += f"**First blood!** \nYou are the first to submit `{flag.flag}` and have earned a bonus 10% \nTotal reward `{reward}` rather than `{flag.value}`\n"
            # logger.debug(msg)
            # await ctx.send(msg)
        
        solve = db.Solve(user=user, flag=flag, value=reward)
        # user.score += reward

        # create a transaction for this solve
        botuser = db.User.get(name=username(bot.user))
        trans = db.Transaction(recipient=user, sender=botuser, value=reward, type='solve', solve=solve, message=flag.description)

        # was this a BYOC Challenge? if so create the reward for the author
        if flag.byoc == True:
            author_reward = db.Transaction(recipient=flag.author, sender=botuser, value=flag.reward * .25, type="byoc reward", message=f'{user.name} of {user.team.name} submitted {flag.flag}')

        db.commit()

        msg += f'Your score is now `{db.getScore(user)}`'
        logger.debug(msg)
        await ctx.send(msg)

@bot.command(name='tip', help="send a tip (points) to another player e.g. !tip @user <some_points> ['some message here']")
async def tip(ctx, target_user: Union[discord.User,str] , tip_amount: float, msg=None):
    # logger.debug(username(target_user))

    if msg == None:
        msg  = "Thank you for being a friend." # make this a random friendly message?

    if tip_amount < 0:
        await ctx.send("nice try... ")
        return

    with db.db_session:

        sender = db.User.get(name=username(ctx))
        
        # check funds
        funds = db.getScore(sender)
        if funds < tip_amount:
            await ctx.send(f"You only have {funds} points")
            return
        
        
        recipient = db.User.get(name=username(target_user))
        if recipient == None:
            await ctx.send(f"invalid recipient...`{target_user}`")
            return 

        credit = db.Transaction(     
            sender=sender, 
            recipient=recipient,
            value=tip_amount,
            type='tip credit',
            message=msg,
        )

        debit = db.Transaction(     
            sender=recipient, 
            recipient=sender,
            value=tip_amount * -1,
            type='tip debit',
            message=msg,
        ) 

        db.commit()
            
    recipient_discord_user = await getDiscordUser(ctx, username(target_user))

    await ctx.send(f'<@{ctx.author.id}> is sending a tip of `{tip_amount}` points to <@{recipient_discord_user.id}> with message ```{msg}```')
    # await ctx.send("this is not implemented yet... just testing the UI/UX")

@bot.command(name='unsolved', help="list only the challenges that your team HASN'T solved", aliases=['usol', 'un', 'unsol'])
async def list_unsolved(ctx):
    with db.db_session:
        user = db.User.get(name=username(ctx))
        challs = db.get_unsolved_challenges(user)

        # logger.debug(challs)

        res = []
        for c in challs:
            res.append([c.id, c.author.name, c.title])

    res.insert(0, ['ID', "Author", "Title"])
    table = AsciiTable(res)

    # logger.debug("discord",challs)
    await ctx.send(f'Showing all unsolved challenges```{table.table}```')

@bot.command(name="all_challenges", help="list all visible challenges. solved or not. ", aliases=['all', 'allc','ac'])
async def list_all(ctx):
    with db.db_session:
        user = db.User.get(name=username(ctx))
        challs = db.get_all_challenges(user)

        res = []
        for c in challs:
            res.append([c.id, c.author.name, c.title])

    res.insert(0, ['ID', "Author", "Title"])
    table = AsciiTable(res)

    # logger.debug("discord",challs)
    await ctx.send(f'Showing all unlocked challenges```{table.table}```')

@bot.command(name='view', help='view a challenge by id e.g. !view <chall_id>', aliases=['vc','v'])
async def view_challenge(ctx, chall_id:int):
    try: 
        chall_id = int(chall_id)
        if chall_id <= 0: 
           raise ValueError
    except (ValueError, BaseException) as e:
        msg = f'invalid challenge id: `{chall_id}`'      
        logger.debug(e, msg)
        await ctx.send(msg)
        return

    with db.db_session:
        user = db.User.get(name=username(ctx))
        # is it unlocked for this user? 
        chall = db.Challenge.get(id=chall_id)
        if db.challegeUnlocked(user, chall):
            author = await getDiscordUser(ctx, chall.author.name)
            msg = f'viewing challenge ID: `{chall_id}` by author <@{author.id}>\n'
            # msg += f'\nTitle`{chall.title}`\nDescription```{chall.description} ```'
            res = {}
            res['challenge_title'] = chall.title
            res['challenge_description'] = chall.description
            res['value'] = db.challValue(chall)
            msg += renderChallenge(res)
        else:
            msg = "challenge doesn't exist or isn't unlocked yet"
        
    await ctx.send(msg)

@bot.command(name="buy_hint", help="buy a hint for a specific challenge e.g. !buy_hint <challenge_id>")
async def buy_hint(ctx, challenge_id: int):
    pass

@bot.command(name='logs', help='show a list of all transactions you are involved in. (solves, hints, tips)', aliases=['log','transactions'])
async def logs(ctx):
    msg  = "" 
    with db.db_session:
        ts = list(db.select((t.value,t.type,t.sender.name, t.recipient.name,t.message,t.time) for t in db.Transaction if username(ctx) == t.recipient.name or username(ctx) == t.sender.name))

    ts.insert(0, ["Value", 'Type','Sender', 'Recipient', 'Message', 'Time'])
    table = AsciiTable(ts)
    
    msg += f'Your Transaction Log ```{table.table}```'

    await ctx.send(msg)

@bot.command(name='solves', help="show all of the flags you have submitted", aliases=['flags'] )
async def solves(ctx):
    msg ="" 
    with db.db_session:
        user = db.User.get(name=username(ctx))

        teammates = db.getTeammates(user)
        solved = []
        for teammate in teammates:
            solved += list(db.select(solve for solve in db.Solve if teammate.name == solve.user.name))
        res = [(solve.flag.flag, [c.id if type(c.title) != 'str' else "Bonus" for c in list(solve.flag.challenges)][0] ,'\n'.join([c.title if type(c.title) != 'str' else "Bonus" for c in list(solve.flag.challenges)]), solve.user.name, solve.time)  for solve in solved]
        
        res.insert(0, ["Flag", "C_ID", "Challenge Title", "User", "Solve Time"])
        table = AsciiTable(res)
        table.inner_row_border = True
        msg += f"`{user.team.name}`'s solves ```{table.table}```"

    await ctx.send(msg)

@bot.command(name='byoc_stats', help="this will show you stats about the BYOC challenges you've created. total profit from solves, etc.")
async def byoc_stats(ctx):
    await ctx.send("your stats")

async def loadBYOCFile(ctx):
    if len(ctx.message.attachments) != 1:
        await ctx.send("You didn't attach the json file...")
        return {}


    # await ctx.send("testing your challenge")

    raw = await ctx.message.attachments[0].read()
    raw = raw.decode()

    try:
        challenge_object = json.loads(raw) # how do we get the challenge object loaded? 
    except json.JSONDecodeError as e:
        await ctx.send("Error decoding json. check syntax ")
        return {}

    return challenge_object    



@bot.command(name="byoc_check", help="this will check your BYOC challenge is valid. It will show you how much it will cost to post")
async def byoc_check(ctx):
    
    challenge_object = await loadBYOCFile(ctx)

    challenge_object['author'] = username(ctx)

    # logger.debug(f"challenge:  {challenge_object}")

    result = db.validateChallenge(challenge_object) # if valid
    # result = {
        # 'valid': False,
        # 'author': None,
        # 'tags': [],
        # 'challenge_title': "",
        # 'challenge_description': "",
        # 'flags': [],
        # 'hints': [],
        # 'value': 0, # sum of flags
        # 'cost': 0
    # }
    if result['valid'] == True:
        msg = renderChallenge(result, preview=True)
        await ctx.send(msg)
    else:
        await ctx.send(f"challenge invalid. Ensure that all required fields are present. see example_challenge.json\n\nfail_reason:{result['fail_reason']}")

@bot.command(name="byoc_commit", help="this will commit your BYOC challege. You will be charged a fee and will have to confirm the submission")
async def byoc_commit(ctx):
    challenge_object = await loadBYOCFile(ctx)
    channel = ctx.channel

    def check(msg):
        return msg.content == 'confirm' and msg.channel == channel
        #TODO  https://discordpy.readthedocs.io/en/latest/api.html#discord.Client.wait_for
    
    
    if result['valid'] == True:
        chall_preview = renderChallenge(result, preview=True)
        await ctx.send(chall_preview)
        await ctx.send("reply with `confirm` in the next 60 seconds to publish your challenge.")
        resp = await discord.ext.commands.Bot.wait_for(ctx, 'message', check=check, timeout=60)
        if resp == 'confirm':
            db.buildChallenge(result)
        else:
            await ctx.send("Cancelling...")
    else:
        await ctx.send(f"challenge invalid. Ensure that all required fields are present. see example_challenge.json\n\nfail_reason:{result['fail_reason']}")

    
    await ctx.send("committing to your challenge; waiting for your confirmation.")
    await ctx.send("It will cost xxx points to post")


# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return # prevent self-spamming

#     keywords = ['test', 'help' ]

#     for keyword in keywords:
#         if keyword in message.content.lower():
#             logger.debug(f'responding to {message.author.display_name} about {keyword}')
#             response = "right or wrong"
#             # await message.author.send('adsf') # send a direct message to the user
#             await message.channel.send(response)
#             break


bot.run(DISCORD_TOKEN)