import os
import random
import datetime
import json

import requests
from terminaltables import AsciiTable
import discord
from discord.ext import commands

from secrets import DISCORD_TOKEN
import database as db


import json

from settings import SETTINGS



bot = commands.Bot(command_prefix='!')

def username(ctx):
    if hasattr(ctx, "author"): 
        return ctx.author.name+ctx.author.discriminator
    elif type(ctx) == discord.User:
        return ctx.name+ctx.discriminator

@bot.event
async def on_ready():
    print(f'{bot.user.name} is online and awaiting your command!')

@db.db_session()
@bot.command(name='register', help='register on the scoreboard. !register <teamname>')
async def register(ctx, teamname):
    if SETTINGS['registration'] == 'disabled':
        await ctx.send("registration is disabled")
        return
    # print('Registering ', ctx.author.name , type(ctx.author.name), )
    # users = db.select([u, type(u),dir(u)] for u in db.User)
    # print(users)

    # is registration open? 
    
    # settings = json.loads(open('settings.json').read())
    # if settings['registration'].lower() == 'disabled':
    #     await ctx.send('self-registration is disabled')
    #     return


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
        print(msg)
        await ctx.send(msg)



@bot.command(name='status', help="shows status information about the CTF")
async def status(ctx):

    msg = SETTINGS

    msg = f"CTF start time \t\t\t\t`{SETTINGS['ctf_start']}`\n"
    msg += f"CTF end time \t\t\t\t`{SETTINGS['ctf_end']}`\n"
    msg += f"CTF paused \t\t\t\t`{SETTINGS['ctf_paused']}`\n"
    msg += f"CTF status message \t\t\t\t`{SETTINGS['status']}`\n"
    await ctx.send(msg)


@bot.command(name='scores', help='shows your indivivually earned points, your teams collective points, and the top 3 teams without their scores. ')
async def scores(ctx):
    # individual score
    msg = ''
    with db.db_session:
        user = db.select(user for user in db.User if username(ctx) == user.name).first()
        # print(user, type(user), dir(user))\
        
        points = db.getScore(user)

        msg += f'Your score is `{points}`\n'
        # teammates scores
        teammates = db.getTeammateScores(user)
        teammates.insert(0, ['Teammate', 'Score'])
        table = AsciiTable(teammates)
        msg += f'\nTeam `{user.team.name}` scores ```{table.table}```\n'
        
        await ctx.send(msg)


        if SETTINGS['scoreboard'] == 'public':
            #top 3 team scores
            scores = db.getTopTeams(num=3)
            scores.insert(0, ['Team Name', 'Score'])
            table = AsciiTable(scores)
            
            msg += f'Top 3 Team scores \n```{table.table}```'

            # top players in the game
            topPlayers = db.topPlayers(num=4)
            data = [(p.name, p.team.name, v) for p,v in topPlayers]
            data.insert(0, ['Player', 'Team', 'Score'])
            table = AsciiTable(data)
            msg += f'Top 4 Players\n```{table.table}```'

            await ctx.send(msg)



@bot.command(name='submit', help='submit a flag e.g. !submit FLAG{TESTFLAG}')
# @bot.command()
# @commands.has_role("CTF_player")
async def submit(ctx, submitted_flag: str = None):

    if submitted_flag == 'FLAG{TESTFLAG}':
        ctx.send("You have submitted the test flag successfuly...")
        return 

    print(f"{username(ctx)} is attempting to submit '{submitted_flag}'")
    
    with db.db_session:
        # is this a valid flag
        res = list(db.select(flag for flag in db.Flag if submitted_flag == flag.flag))
        # print('res', type(res), len(res), res)

        if len(res) == 0:
            msg = f'incorrect: we got "{submitted_flag}"'
            print(msg)
            await ctx.send(msg)
            return

        user = db.User.get(name=username(ctx))
        flag = res[0]

        # have I already submitted this flag?
        solves = list(db.select(solve for solve in db.Solve if submitted_flag == solve.flag.flag and username(ctx) == solve.user.name)) # should be an empty list 

        if len(solves) > 0: 
            msg = f"You've already submitted `{submitted_flag}` at {solves[0].time} "
            print(msg)
            await ctx.send(msg)
            return

        # has a teammate submitted this flag? 

        teammates = db.getTeammates(user)
        solved = []
        for teammate in teammates:
            res = list(db.select(solve for solve in db.Solve if submitted_flag == solve.flag.flag and teammate.name == solve.user.name))

            # print('res = ', res)
            if len(res) > 0: # already submitted by a teammate 
                msg = f"{res[0].user.name} already submitted `{submitted_flag}` at {res[0].time} "
                print(msg)
                await ctx.send(msg)
                return
        
         # if I get this far, it has not been solved by any of my team

        msg = "Correct!\n"

        challenge = db.select(c for c in db.Challenge if flag in c.flags).first()
        
        if challenge:     # was this flag part of a challenge? 
            # print("challenge: ", challenge, type(challenge), dir(challenge))
            msg += f'You submitted a flag for challenge `{challenge.title}`.\n'
        
        
        reward = flag.value 
        if flag.unsolved == True:
            
            reward += flag.value * .1
            flag.unsolved = False
            msg += f"**First blood!** \nYou are the first to submit `{flag.flag}` and have earned a bonus 10% \nTotal reward `{reward}` rather than `{flag.value}`\n"
            # print(msg)
            # await ctx.send(msg)
        
        solve = db.Solve(user=user, flag=flag, value=reward)
        # user.score += reward
        db.commit()

        msg += f'Your score is now `{db.getScore(user)}`'
        print(msg)
        await ctx.send(msg)

@bot.command(name='tip', help="send a tip (in points) to another player e.g. !tip @user <some_points> ['some message here']")
async def tip(ctx, target_user: discord.User , tip_amount: float, msg=None):
    # print(username(target_user))

    if msg == None:
        msg  = "Thank you for being a friend." # make this a random friendly message. 

    await ctx.send(f'<@{ctx.author.id}> is sending a tip of `{tip_amount}` points to <@{target_user.id}> with message ```{msg}```')
    await ctx.send("this is not implemented yet... just testing the UI/UX")




# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return # prevent self-spamming

#     keywords = ['test', 'help' ]

#     for keyword in keywords:
#         if keyword in message.content.lower():
#             print(f'responding to {message.author.display_name} about {keyword}')
#             response = "right or wrong"
#             # await message.author.send('adsf') # send a direct message to the user
#             await message.channel.send(response)
#             break


bot.run(DISCORD_TOKEN)