#!/usr/bin/env python3
og_print = print
import random
from rich import print
from fileinput import filename
from logging import log
from pony.orm.core import args2str
from settings import SETTINGS, init_config, is_initialized
import datetime
import time
import json
import pyfiglet

from typing import Union

import hashlib

from loguru import logger

logger.add(SETTINGS["_logfile"])

import requests
from terminaltables import AsciiTable, GithubFlavoredMarkdownTable
import discord
from discord.ext import commands

import asyncio
import database as db

import toml

FIRST_PLACE_TEAM = ""


def banner():
    ret = _spray(msg="byoctf")
    msg = f"""
{ret}

by fs2600 / SOTB crew                                                                   
    """
    og_print(msg)


# should be handled in settings now.
# if is_initialized() == False: # basically the ./byoctf_diskcache/cache.db has data in it. rm to reset
#     init_config()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


async def newLeader() -> bool:
    global FIRST_PLACE_TEAM
    ctf_chan = bot.get_channel(SETTINGS["_ctf_channel_id"])
    leader = db.getTopTeams(num=1)[0]
    if leader[0] != FIRST_PLACE_TEAM:
        FIRST_PLACE_TEAM = leader[0]
        await ctf_chan.send(
            f"There's a new Leader!!! `{leader[0]}` with `{leader[1]}` points"
        )
        # this is a hook point for calling the lights api to do something on leader change...
        return True
    return False


@db.db_session
def getDecayChallengeValue(chall_id: id) -> tuple[int, int, float]:
    raise NotImplementedError
    chall = db.Challenge[chall_id]

    solve_count = db.count(
        db.select(t for t in db.Transaction if t.flag == flag).without_distinct()
    )

    team_count = (
        db.count(db.select(t for t in db.Team)) - 1
    )  # don't count discordbot's team

    solve_percent = solve_count / team_count

    reward *= max(
        [1 - solve_percent, SETTINGS["_decay_minimum"]]
    )  # don't go below the minimum established

    return solve_count, team_count, reward


@bot.event
async def on_ready():
    logger.debug(f"{bot.user.name} is online and awaiting your command!")


def username(obj):
    if hasattr(obj, "author"):
        return f"{obj.author.name}"
    elif type(obj) == discord.User or type(obj) == discord.user.ClientUser:
        return f"{obj.name}"

    return "__NONE__"


def ctfRunning():
    the_time = datetime.datetime.utcnow()
    if SETTINGS["ctf_paused"]:
        return False

    if (SETTINGS["ctf_start"] == -1 or SETTINGS["ctf_start"] <= time.time()) and (
        SETTINGS["ctf_end"] == -1 or SETTINGS["ctf_end"] >= time.time()
    ):
        return True

    return False


async def getDiscordUser(ctx, target_user: str):
    # this is only for the gui representation of the recipient
    # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.UserConverter
    logger.debug(f"looking up user {target_user}")
    uc = discord.ext.commands.UserConverter()
    try:
        res = await uc.convert(ctx, target_user)
    except BaseException as e:
        logger.debug(e)
        res = target_user
    logger.debug(f"{res=}, {type(res)}")
    return res


async def sendBigMessage(ctx, content, wrap=True):
    """this should split a long message across multiple sends if it exceeds the 2000 char limit of discord. requires newlines in the message. Set wrap=False to omit the code blocks for your message"""
    lines = content.splitlines(keepends=True)
    if SETTINGS["_debug"] == True and SETTINGS["_debug_level"] > 1:
        logger.debug(content)
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) < 1800:
            chunk = chunk + line
        else:
            if wrap:
                await ctx.send(f"```{chunk}```")
            else:
                await ctx.send(f"{chunk}")
            chunk = line

    # send final chunk
    if wrap:
        await ctx.send(f"```{chunk}```")
    else:
        await ctx.send(f"{chunk}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(
            f"Command `{ctx.message.content}` not found... \n\nTry `!help` or `!help <command>`"
        )
    # elif isinstance(error, commands.errors.BadArgument):
    #     await ctx.send(f'Invalid argument to command')
    elif isinstance(error, commands.errors.CommandOnCooldown):
        msg = f"***Whoa... Slow down... Please try again in {error.retry_after:.2f}s***"
        await ctx.send(msg)
        logger.debug(f"Brute forcing for flags? - {username(ctx)}: {msg}")
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f"Missing argument to command")
    else:
        logger.debug(f"{error}")
        # if SETTINGS["_debug"]:
        raise error


async def inPublicChannel(
    ctx, msg="this command should only be done in a private message (a DM) to the bot"
):
    if ctx.channel.type.name == "text":
        # we're in public
        await ctx.message.delete()
        await ctx.send(msg)
        return True
    return False


async def isRegistered(
    ctx, msg="It doesn't look like you're registered yet. `!reg <teamname> <teampass>`"
):
    with db.db_session:
        user = db.User.get(name=username(ctx))
        if user == None:
            await ctx.send(msg)
            return False
    return True


def renderChallenge(result: dict, preview=False):
    """returns the string to be sent to the user via discord. preview is mostly for BYOC challenges to validate that flags came through correctly."""
    msg = ""

    # preview is for the rendering of the validator for byoc challenges
    if preview == True:
        if result.get("valid"):
            msg = f"Challenge **valid**.  😎😎😎 \n\n"
        else:
            msg = f"Challenge ***INVALID***. ❌❌❌ \n\n **failed because**: {result['fail_reason']}\n\n"

        byoc_rate = SETTINGS.get("_byoc_reward_rate", 0)
        break_even_solves = (result["cost"] / byoc_rate) // 100

        msg += f"{'-'*25}\n\n"
        msg += "Here's a preview:\n\n"
        msg += f"It will cost `{result['cost']}` points to post with `!byoc_commit`\n"

    # normal challenge rendering
    # print(result)
    msg += "-" * 40 + "\n"
    msg += f"**Title**: `{result['challenge_title']}`\n\n"
    msg += f"**Total Challenge Value**: `{result['value']}` points\n\n"
    msg += f'**Challenge_uuid**: `{result.get("uuid")}`\n\n'

    # byoc validation rendering
    if preview == True:
        msg += f"Reward rate is currently `{byoc_rate}` of flag value which means about `{break_even_solves}` solves will be required to break even.\n\n"

    # normal rendering
    msg += f"**Description**:\n{result['challenge_description']}\n\n"
    msg += f"**Tags**: ` {', '.join(result.get('tags',list()))} `  \n\n"
    msg += f"**Unlocked By Challenges**:  `{result.get('parent_ids', list())}`\n\n"
    msg += "-" * 40 + "\n\n"

    msg += f'**Number of Flags**: {result.get("num_flags",0)}\n\n'
    msg += f"**Total Hints**: {len(result.get('hints',list()))}\n\n"
    for idx, hint in enumerate(result.get("hints_purchased", list()), 1):
        msg += f"**Hint** {idx}: {hint.text}\n"
    msg += "-" * 40 + "\n\n"
    if result.get("byoc_ext_url") != None:
        msg += f"**This is an externally validated flag:** Players must submit it with `!byoc_ext <chall_id> <flag>` "

    # more byoc validation rendering
    if preview == True:
        msg += f"\n**Hints**\n\n"
        for idx, hint in enumerate(result.get("hints", list()), 1):
            msg += (
                f"   - Hint {idx}: `{hint['hint_text']}` Cost: `{hint['hint_cost']}` \n"
            )

        msg += f"\n\n"
        msg += "-" * 40 + "\n"

        msg += f"\n**Flags**\n\n"
        for idx, flag in enumerate(result["flags"], 1):
            msg += f"   - Flag {idx}: `{flag['flag_flag']}` value: `{flag['flag_value']}` title: `{flag['flag_title']}` \n"

    # finally send it back.
    return msg


# TODO this might be a problem; disable team unregistration...
# user1 joins team A
# user1 joins team A
# user2 joins team A
# user1 creates a challenge X
# user2 leaves team A
# user2 joins team B (a burner team)
# user2 solves challenge X
# user2 leaves team B
# user2 joins team A


@db.db_session()
@bot.command(
    name="unregister",
    help="Leave a team... you still exist as a player but without a team... no fun.",
    aliases=["unreg", "leave"],
)
@commands.dm_only()
async def unregister(ctx: discord.ext.commands.Context):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't leave a team in public channels..."
    ):
        return

    await ctx.send("registration is disabled... you pesky hackers ruined it..")
    return  # this may be deprecated or removed in the future...
    if SETTINGS["registration"] == "disabled":
        await ctx.send("registration is disabled")
        return
    with db.db_session:
        user = db.User.get(name=username(ctx))

        if user == None:
            logger.debug(f"user {username(ctx)} not registered to play.")
            await ctx.send("You weren't registered")
            return

        if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 0:
            logger.debug(f"{user.name} left team {user.team.name}")

        await ctx.send(f"Leaving team {user.team.name}... bye.")
        unaffiliated = db.Team.get(name="__unaffiliated__")
        user.team = unaffiliated
        db.commit()


def _spray(msg: str = "BYOCTF \nby fs2600 ") -> str:
    fonts = [
        "3-d",
        "3x5",
        "5lineoblique",
        "slant",
        "5lineoblique",
        "alphabet",
        "banner3-D",
        "doh",
        "isometric1",
        "letters",
        "alligator",
        "bubble",
    ]

    return pyfiglet.figlet_format(msg, font=random.choice(fonts))


@bot.command(name="spray", help="show a random byoctf banner")
async def spray(ctx: discord.ext.commands.Context, msg: str = "BYOCTF \nby fs2600 "):
    ret = _spray(msg=msg)
    count = 0
    while len(ret) > 2000:
        ret = _spray(msg=msg)
        if count > 4:
            await ctx.send("message may be too long... try something else")
            return
    await ctx.send(f"```{ret}```")


@db.db_session()
@bot.command(
    name="register",
    help="register on the scoreboard. !register <teamname> <password>; wrap team name in quotes if you need a space",
    aliases=["reg", "join"],
)
@commands.dm_only()
async def register(
    ctx: discord.ext.commands.Context, teamname: str = "", password: str = ""
):
    # if await isRegistered(ctx, msg="Looks like you're already registered.... try `!unreg`") == False:
    #     return

    if await inPublicChannel(
        ctx,
        msg=f"Hey, <@{ctx.author.id}>, don't register or join a team in public channels...",
    ):
        return

    if SETTINGS["registration"] == "disabled":
        await ctx.send("registration is disabled")
        return

    if teamname == "" or password == "":
        await ctx.send(
            "I know it looks like the teamname and password are optional parameters, but they aren't... sorry. wrap the team name in quotes if it has spaces. "
        )
        return

    # db.register_team(teamname, password, username(ctx)) 
    # # TODO move over to using this function to separate discord from business logic 16SEP23
    with db.db_session:
        teamname = teamname.strip()
        password = password.strip()
        hashed_pass = hashlib.sha256(password.encode()).hexdigest()

        team = db.Team.get(name=teamname)
        unafilliated = db.Team.get(name="__unaffiliated__")
        user = db.User.get(name=username(ctx))

        if user == None:
            user = db.User(name=username(ctx), team=unafilliated)
            db.rotate_player_keys(user)

        if user.team.name != "__unaffiliated__":
            msg = f"already registered as `{username(ctx)}` on team `{user.team.name}`. talk to an admin to have your team changed..."
            await ctx.send(msg)
            if SETTINGS["_debug"]:
                logger.debug(msg)
            return

        # does the team exist?
        if team == None:
            team = db.Team(name=teamname, password=hashed_pass)
            pub,priv = db.generate_keys()
            team.public_key = pub
            team.private_key = priv

        if len(team.members) == SETTINGS["_team_size"]:
            msg = f"No room on the team... currently limited to {SETTINGS['_team_size']} members per team."
            await ctx.send(msg)
            if SETTINGS["_debug"]:
                logger.debug(msg)
            return

        if (
            hashed_pass != team.password
        ):  # if it's a new team, these should match automatically..
            msg = f"Password incorrect for team {team.name}"
            await ctx.send(msg)

            if SETTINGS["_debug"]:
                logger.debug(
                    f"{username(ctx)} failed registration; Team {teamname} pass {password} hashed {hashed_pass}"
                )
            return

        user.team = team
        db.commit()

    # give them the 'byoctf' channel on Arkansas hackers
    # add them to the appropriate channels on your server.
    guild: discord.Guild = bot.get_guild(SETTINGS["_ctf_guild_id"])

    role = guild.get_role(SETTINGS["_ctf_channel_role_id"])
    channel = bot.get_channel(SETTINGS["_ctf_channel_id"])

    member = guild.get_member(ctx.author.id)
    if member == None:
        msg = f"Error {member=}"
        logger.debug(msg)
        # await ctx.send(msg)
        return None
    await member.add_roles(role)

    if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 0:
        logger.debug(f"{member} on {guild} got role {role}")

    msg = f"Registered as `{username(ctx)}` on team `{teamname}`. Check the {channel.mention} channel"
    await ctx.send(msg)
    


@bot.command(
    name="ctfstatus",
    help="shows status information about the CTF",
    aliases=["ctfstat", "ctfstats"],
)
async def ctfstatus(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx,
        msg=f"Hey, <@{ctx.author.id}>, don't view ctf status info in public channels...",
    ):
        return

    data = [
        (k, SETTINGS[k]) for k in SETTINGS.iterkeys() if k[0] != "_"
    ]  # filter out the private settings; see settings.py config object
    data.insert(0, ["Setting", "Value"])
    table = GithubFlavoredMarkdownTable(data)
    await ctx.send(f"CTF Status ```{table.table}```")


@bot.command(
    name="scores",
    help="shows your indivivually earned points, your teams collective points, and the top N teams without their scores.",
    aliases=["score", "points", "top"],
)
# @commands.dm_only()
async def scores(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx,
        msg=f"Hey, <@{ctx.author.id}>, don't show your scores in public channels...",
    ):
        return

    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return

    if await newLeader() == True:
        # another hook for doing intersting stuff with lights and sound when there is a new score leader
        pass

    # individual score
    msg = ""
    with db.db_session:
        user = db.User.get(name=username(ctx))  # simpler

        individual_points = db.getScore(user)
        if SETTINGS["_debug"] == True and SETTINGS["_debug_level"] == 2:
            logger.debug(f"{user.name} individual points {individual_points}")

        # teammates scores
        teammates = db.getTeammateScores(user)
        teammates = sorted(teammates, key=lambda x: x[1], reverse=True)
        teammates.insert(0, ["Teammate", "Score"])
        table = GithubFlavoredMarkdownTable(teammates)

        team_points = sum([v for k, v in teammates[1:]])  # skip header

        msg += f"Your score is `{individual_points}`\n"
        msg += f"\nTeam `{user.team.name}` has `{team_points}` ```{table.table}```"

        if SETTINGS["scoreboard"] == "public":
            # top 3 team scores
            scores = db.getTopTeams(
                num=SETTINGS["_scoreboard_size"]
            )  # private settings with _
            scores.insert(0, ["Team Name", "Score"])
            table = GithubFlavoredMarkdownTable(scores)

            msg += (
                f'Top {SETTINGS["_scoreboard_size"]} Team scores \n```{table.table}```'
            )
        else:
            msg += f"Scoreboard is set to private\n"

        if SETTINGS["_show_mvp"] == True:
            # top players in the game
            topPlayers = db.topPlayers(num=SETTINGS["_mvp_size"])
            data = [(p.name, p.team.name, v) for p, v in topPlayers]
            data.insert(0, ["Player", "Team", "Score"])
            table = GithubFlavoredMarkdownTable(data)
            msg += f'Top {SETTINGS["_mvp_size"]} Players\n```{table.table}```'
        else:
            msg += f"MVP is set to False    "

        await ctx.send(msg)


@bot.command(
    name="whoami", help="Show username,api_key, and teamname", aliases=["w"]
)  # shows authorid, name, teamname
async def byoc_stats(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(ctx, msg=f"<@{ctx.author.id}>, dm this command to CTFBot"):
        return

    msg = ""
    with db.db_session:
        user = db.User.get(name=username(ctx))
        teammates = db.getTeammates(user)

    await ctx.send(
        f"AuthorID:  <@{ctx.author.id}>\nUserName:   {user.name}\napi key:    {user.api_key}\nHUD Link: https://scoreboard.byoctf.com/login/{user.api_key}\nTeamName: {user.team.name}\nTeammates: {[t.name for t in teammates]}\n\nuse `!mykeys` to see your pub/priv keys or `!rotate_keys` to generate new ones."
    )

@bot.command(name="mykeys", help="Show public and private keys")
async def my_keys(ctx):
    with db.db_session:
        user = db.User.get(name=username(ctx))
        await ctx.send(f"```Public Key:\n{user.public_key}```")
        await ctx.send(f"```Private Key:\n{user.private_key}```")



@bot.command(
    name="submit", help="submit a flag e.g. !submit FLAG{some_flag}", aliases=["sub"]
)
@commands.cooldown(
    1, SETTINGS["_rate_limit_window"], type=discord.ext.commands.BucketType.user
)  # one submission per second per user
async def submit(ctx: discord.ext.commands.Context, submitted_flag: str = None):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't submit flags in public channels..."
    ):
        return

    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return

    if SETTINGS["_debug"] == True and SETTINGS["_debug_level"] == 1:
        logger.debug(f"{username(ctx)} is attempting to submit '{submitted_flag}'")

    with db.db_session:
        # is this a valid flag
        flag = db.Flag.get(flag=submitted_flag)
        user = db.User.get(name=username(ctx))

        if flag == None:
            msg = f'incorrect: we got "{submitted_flag}"'
            logger.debug(msg)
            await ctx.send(msg)
            return

        # have I already submitted this flag?
        solves = list(
            db.select(  # type: ignore
                solve
                for solve in db.Solve  # type: ignore
                if submitted_flag == solve.flag.flag
                and username(ctx) == solve.user.name
            )
        )  # should be an empty list

        if len(solves) > 0:  # if prev_solve != None:
            msg = f"You've already submitted `{submitted_flag}` at {solves[0].time} "
            logger.debug(msg)
            await ctx.send(msg)
            return

        # has a teammate submitted this flag?
        teammates = db.getTeammates(user)
        solved = list()
        for teammate in teammates:
            res = list(
                db.select(  # type: ignore
                    solve
                    for solve in db.Solve  # type: ignore
                    if submitted_flag == solve.flag.flag
                    and teammate.name == solve.user.name
                )
            )  # see above regarding simpler looking query

            if len(res) > 0:  # already submitted by a teammate
                msg = f"{res[0].user.name} already submitted `{submitted_flag}` at {res[0].time} "
                if SETTINGS["_debug"] == True and SETTINGS["_debug_level"] == 1:
                    logger.debug(msg)
                await ctx.send(msg)
                return

        # did this user author the flag?
        if flag.author.name == user.name:
            await ctx.send("You can't submit a flag from your own challenges...")
            return
        # did someone else on their team author this flag?
        for teammate in teammates:
            if flag.author.name == teammate.name:
                await ctx.send(
                    "You can't submit a flag created by someone on your own team..."
                )
                return

        # if I get this far, it has not been solved by any of my teammates

        # is this challenge unlocked?
        # get parent challenges.
        flag_challs = list(flag.challenges)
        # incomplete_challs = list()
        for chall in flag_challs:
            for p_chall in list(chall.parent):
                print(p_chall.title, p_chall.id)
                # is the parent complete?
                # if db.challegeUnlocked(user, chall) == False:
                if db.challengeComplete(p_chall, user) == False:
                    # incomplete_challs.append(p_chall)
                    await ctx.send(
                        f"This flag is for a challenge that is not unlocked yet... good job? Look at `{p_chall.title}` and unlock it (50% or more flags captured) then try again?"
                    )
                    # return

        msg = "Correct!\n"
        reward = flag.value

        challenge: db.Challenge = db.select(  # type: ignore
            c for c in db.Challenge if flag in c.flags
        ).first()

        if challenge:  # was this flag part of a challenge?
            msg += f"You submitted a flag for challenge `{challenge.title}`.\n"

        if flag.unsolved == True:
            ctf_chan = bot.get_channel(SETTINGS["_ctf_channel_id"])
            discord_user = await getDiscordUser(ctx, user.name)
            logger.debug(f"{discord_user=} {type(discord_user)}")
            await ctf_chan.send(f"<@{discord_user.id}> drew First Blood!")
            msg += f'**First blood!** \nYou are the first to submit `{flag.flag}` and have earned a bonus {SETTINGS["_firstblood_rate"] * 100 }% \nTotal reward `{flag.value * (1 + SETTINGS["_firstblood_rate"])}` rather than `{flag.value}`\n'
        elif SETTINGS["_decay_solves"] == True:
            # solve_count, team_count, decay_value = getDecayValue(challenge.id)
            solve_count = db.count(
                db.select(  # type: ignore
                    t for t in db.Transaction if t.flag == flag
                ).without_distinct()
            )

            team_count = (
                db.count(db.select(t for t in db.Team)) - 1
            )  # don't count discordbot's team

            solve_percent = solve_count / team_count

            reward *= max(
                [1 - solve_percent, SETTINGS["_decay_minimum"]]
            )  # don't go below the minimum established

            if SETTINGS["_debug"] == True:
                logger.debug(
                    f"decay solves {solve_count} team count{team_count} ; solve percent {solve_percent} reward is {reward}"
                )

            msg += f"{solve_count} teams have solved this challenge... Your reward is reduced based on that fact... reward is {reward} rather than {flag.value}\n"

        # firstblood and decay points/award/reductions logic is now in create solve. above is for display only
        db.createSolve(
            user=user,
            flag=flag,
            challenge=challenge,
            msg="\n".join([c.title for c in flag.challenges]),
        )

        msg += f"Challenge is {db.percentComplete(challenge, user)}% complete.\n"
        msg += f"Your score is now `{db.getScore(user)}`"
        # logger.debug(msg)
        await ctx.send(msg)

@bot.command(
    name="rotate_keys",
    help="generate new api_key, public_key, and private_key",
)
@commands.cooldown(
    1, SETTINGS["_rate_limit_window"], type=discord.ext.commands.BucketType.user
)  # one submission per second per user
async def rotate_keys(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx,
        msg=f"Hey, <@{ctx.author.id}>, send that command in a DM to the bot...",
    ):
        return
    
    def check(msg):
        return msg.content == "confirm" and msg.channel == ctx.channel
        # TODO  https://discordpy.readthedocs.io/en/latest/api.html#discord.Client.wait_for
    
    await ctx.send(
        "\n\n\n***Reply with `confirm` in the next 20 seconds to rotate your api, pub/priv keys***"
    )

    with db.db_session:
        user = db.User.get(name=username(ctx))
        if user == None:
            await ctx.send("invalid user somehow...")
            return
        
        resp = None
        try:
            resp = await ctx.bot.wait_for("message", check=check, timeout=20)
        except asyncio.exceptions.TimeoutError as e:
            await ctx.send("**Cancelling...**")
            return
        if resp.content == "confirm":
            db.rotate_player_keys(user)

            await ctx.send('Keys updated. use `!whoami` to see them... ')
            return
        await ctx.send('invalid response')




@bot.command(
    name="tip",
    help="send a tip (points) to another player; msg has 100 char limit e.g. !tip @user <some_points> ['some message here']",
)
@commands.cooldown(
    1, SETTINGS["_rate_limit_window"], type=discord.ext.commands.BucketType.user
)  # one submission per second per user
async def tip(
    ctx,
    target_user: Union[discord.User, str],
    tip_amount: float,
    msg: str | None = None,
):
    if await isRegistered(ctx) == False:
        return

    if tip_amount <= 0:
        await ctx.send("nice try... ")
        return

    with db.db_session:
        sender = db.User.get(name=username(ctx))

        recipient = db.User.get(name=username(target_user))

        if sender == recipient:
            await ctx.send("nice try... ")
            return

        if recipient == None:
            await ctx.send(
                f"invalid recipient...`{target_user}`. Are they registered for the ctf using the `!reg` command?"
            )
            return

        result, points = db.send_tip(sender, recipient, tip_amount=tip_amount, msg=msg)
        if result == False:
            await ctx.send(
                f"You only have {points} points and can't send {tip_amount}... math is hard... "
            )
            return

        # tip = db.Transaction(
        #     sender=sender,
        #     recipient=recipient,
        #     value=tip_amount,
        #     type="tip",
        #     message=msg,
        # )

        # db.commit()

    recipient_discord_user = await getDiscordUser(ctx, username(target_user))
    message = f"<@{ctx.author.id}> is sending a tip of `{tip_amount}` points to <@{recipient_discord_user.id}> with message ```{msg}```"
    await ctx.send(message)
    if SETTINGS["_debug"] == True and SETTINGS["_debug_level"] == 1:
        logger.debug(f"tip from {username(ctx)} - {message}")


@bot.command(
    name="unsolved",
    help="list only the challenges that your team HASN'T solved",
    aliases=["usol", "un", "unsol"],
)
async def list_unsolved(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't view challenges in public channels..."
    ):
        return

    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return

    with db.db_session:
        user = db.User.get(name=username(ctx))
        challs = db.get_incomplete_challenges(user)

        # logger.debug(challs)

        res = list()
        for c in challs:
            if c.author not in db.getTeammates(
                user
            ):  # you can't solve your teammates challenges, so don't show them.
                res.append(
                    [c.id, c.author.name, c.title, ", ".join([t.name for t in c.tags])]
                )

    res.insert(0, ["ID", "Author", "Title", "Tags"])
    table = GithubFlavoredMarkdownTable(res)

    # logger.debug("discord",challs)\
    msg = f"Showing all unsolved challenges```{table.table}```"

    await ctx.send(msg)


def anyIn(list1, list2):
    return any(elem in list1 for elem in list2)


def allIn(list1, list2):
    return all(elem in list1 for elem in list2)


@bot.command(
    name="all_challenges",
    help="list all visible challenges. solved or not. ",
    aliases=["all", "allc", "ac"],
)
async def list_all(ctx, *, tags=None):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't view challenges in public channels..."
    ):
        return

    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return

    with db.db_session:
        user = db.User.get(name=username(ctx))
        challs = db.get_unlocked_challenges(user)
        # It'd be nice to show a percentage complete as well...
        #
        # don't show teammates challenges or your own challenges. !bstat to see yours. helps prevent a teammate working on your challenges when they couldn't submit it anyway.
        res = list()
        if tags == None:
            res = [
                (
                    c.id,
                    c.author.name,
                    c.title,
                    db.challValue(c),
                    f"{db.percentComplete(c, user)}%",
                    "*"
                    * int(db.avg(r.value for r in db.Rating if r.challenge == c) or 0),
                    ", ".join([t.name for t in c.tags]),
                )
                for c in challs
                if c.id > 0 and c.author not in db.getTeammates(user)
            ]

        else:
            tags = tags.split(" ")
            includes = [x for x in tags if x.startswith("!") == False]
            excludes = [x[1:] for x in tags if x.startswith("!")]

            if SETTINGS["_debug"] and SETTINGS["_debug_level"] >= 1:
                logger.debug(
                    f"tags: {tags}; filter including {includes}; excluding {excludes}"
                )

            for chall in challs:
                chall_tags = [t.name for t in chall.tags]

                if anyIn(
                    excludes, chall_tags
                ):  # kick it back if any of the excludes are in the chall_tags
                    continue

                if (
                    len(includes) > 0 and anyIn(includes, chall_tags) == False
                ):  # if it doesn't have any of the includes, skip it.
                    continue

                if chall.id < 1 or chall.author in db.getTeammates(
                    user
                ):  # other reasons to skip this challenge...
                    continue

                res += [
                    [
                        chall.id,
                        chall.author.name,
                        chall.title,
                        db.challValue(chall),
                        f"{db.percentComplete(chall, user)}%",
                        "*"
                        * int(
                            db.avg(r.value for r in db.Rating if r.challenge == chall)
                            or 0
                        ),
                        ", ".join(chall_tags),
                    ]
                ]

    res.insert(0, ["ID", "Author", "Title", "Total Value", "Done", "Rating", "Tags"])
    table = GithubFlavoredMarkdownTable(res)
    # logger.debug("discord",challs)
    msg = f"Showing all unlocked challenges"
    await ctx.send(msg)
    await sendBigMessage(ctx, table.table)
    #


@bot.command(
    name="view",
    help="view a challenge by id e.g. !view <chall_id> int or uuid",
    aliases=["vc", "v"],
)
async def view_challenge(ctx, chall_id):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't view challenges in public channels..."
    ):
        return
    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return

    if db.is_valid_uuid(chall_id):
        ...
    else:
        try:
            chall_id = int(chall_id)
            if chall_id < 0:
                raise ValueError
        except ValueError as e:
            msg = f"invalid challenge id: `{chall_id}`"
            logger.debug(str(e), msg)
            await ctx.send(msg)
            return
        except BaseException as e:
            logger.debug(e)
            return

    with db.db_session:
        user = db.User.get(name=username(ctx))
        # is it unlocked for this user?
        if db.is_valid_uuid(chall_id):
            chall = db.Challenge.get(uuid=chall_id)
        else:
            chall = db.Challenge.get(id=chall_id)

        if chall != None and db.challegeUnlocked(user, chall):
            author = await getDiscordUser(ctx, chall.author.name)
            if isinstance(author, discord.User):
                msg = f"viewing challenge ID: `{chall_id}` by author <@{author.id}>\n"
            else:
                msg = f"viewing challenge ID: `{chall_id}` by author {author}\n"
            # msg += f'\nTitle`{chall.title}`\nDescription```{chall.description} ```'
            res = {}
            res["challenge_title"] = chall.title
            res["uuid"] = chall.uuid
            res["challenge_description"] = chall.description
            res["parent"] = [c.id for c in list(chall.parent)]
            res["value"] = db.challValue(chall)
            res["hints"] = [h for h in chall.hints]
            res["hints_purchased"] = [
                hint_trans.hint
                for hint_trans in db.getHintTransactions(user)
                if hint_trans.hint.challenge == chall
            ]
            res["byoc_ext_url"] = chall.byoc_ext_url
            res["tags"] = [tag.name for tag in chall.tags]
            res["num_flags"] = len([f for f in chall.flags])
            msg += renderChallenge(res)
        else:
            msg = "challenge doesn't exist or isn't unlocked yet"

    # should we consider using a sendBigMessage?
    msg = db.render_variables(user, msg)
    await sendBigMessage(ctx, msg, wrap=False)
    # await ctx.send(msg)


@bot.command(
    name="buy_hint",
    help="buy a hint for a specific challenge e.g. !buy_hint <challenge_id>",
    aliases=["bh"],
)
async def buy_hint(ctx, challenge_id: int):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't buy hints in public channels..."
    ):
        return

    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return
    with db.db_session:
        user = db.User.get(name=username(ctx))
        hint_cost = db.getHintCost(user, challenge_id)
        if hint_cost < 0:
            await ctx.send(
                f"there are no available hints to purchase for challenge id {challenge_id}"
            )
            return

    await ctx.send(
        f"\n\nA hint for *challenge {challenge_id}* will cost you ***{hint_cost} points***\n\n***Reply with `confirm` in the next 20 seconds to purchase this hint.***"
    )

    def check(msg):
        return msg.content.lower().strip() == "confirm" and msg.channel == ctx.channel
        # TODO  https://discordpy.readthedocs.io/en/latest/api.html#discord.Client.wait_for

    resp = None
    try:
        resp = await ctx.bot.wait_for("message", check=check, timeout=20)
    except asyncio.exceptions.TimeoutError as e:
        await ctx.send("**Cancelling due to timeout...**")
        return
    except BaseException as e:
        logger.debug(e)
        return
    if resp.content != "confirm":
        await ctx.send("**Cancelling due to invalid response...**")

    with db.db_session:
        user = db.User.get(name=username(ctx))
        chall = db.Challenge.get(id=challenge_id)
        # chall.hints
        res, hint = db.buyHint(user=user, challenge_id=challenge_id)
        if res != "ok":
            await ctx.send(res)
            return

        hint_message = f"Here's a hint for Challenge ID {challenge_id} `{chall.title}`\n`{hint.text}`"
        await sendBigMessage(ctx, hint_message, wrap=False)
        await ctx.send("You can view your purchased hints with `!hints`")


@bot.command(name="hints", help="show your purchased hints")
async def show_hints(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't show your hints in public channels..."
    ):
        return

    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return

    with db.db_session:
        user = db.User.get(name=username(ctx))
        hint_transactions = db.getHintTransactions(user)

        msg = f"Team {user.team.name}'s hints:\n"

        data = list()
        teammates = db.getTeammates(user)  # throws an error about db session is over

        for tm in teammates:
            tm_hints = db.getHintTransactions(tm)
            data += [
                (ht.hint.challenge.id, ht.hint.text, ht.hint.cost, ht.sender.name)
                for ht in tm_hints
            ]

        data.insert(0, ["Chall_ID", "Hint", "Cost", "Purchaser"])
        table = GithubFlavoredMarkdownTable(data)

    await sendBigMessage(ctx, f"{msg}{table.table}")


@bot.command(
    name="logs",
    help="show a list of all transactions you are involved in. (solves, purchases, tips, etc.)",
    aliases=["log", "transactions"],
)
async def logs(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't dump logs in public channels..."
    ):
        return

    msg = "Your Transaction Log"
    with db.db_session:
        ts = list(
            db.select(  # type: ignore
                (t.value, t.type, t.sender.name, t.recipient.name, t.message, t.time)
                for t in db.Transaction
                if username(ctx) == t.recipient.name or username(ctx) == t.sender.name
            )
        )

    ts.insert(0, ["Value", "Type", "Sender", "Recipient", "Message", "Time"])
    table = GithubFlavoredMarkdownTable(ts)

    if len(msg + table.table) >= 2000:
        # logger.debug(f'table > 2000 : {len(table.table)} {table.table}')

        await sendBigMessage(ctx, f"{msg}\n{table.table}")
    else:
        msg += f"```{table.table}```"
        await ctx.send(msg)


@bot.command(
    name="solves", help="show all of the flags you have submitted", aliases=["flags"]
)
async def solves(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't show your flags in public channels..."
    ):
        return

    with db.db_session:
        user = db.User.get(name=username(ctx))

        msg = f"`{user.team.name}`'s solves "

        teammates = db.getTeammates(user)
        solved = list()
        for teammate in teammates:
            solved += list(
                db.select(  # type: ignore
                    solve for solve in db.Solve if teammate.name == solve.user.name
                )
            )

        res = list()
        for solve in solved:
            line = (
                solve.flag_text,
                solve.challenge.id,
                solve.challenge.title,
                solve.user.name,
                solve.time,
            )
            res.append(line)

        res.insert(0, ["Flag", "Chall ID", "Chall Title", "User", "Solve Time"])
        table = GithubFlavoredMarkdownTable(res)

        if len(msg + table.table) >= 2000:
            await sendBigMessage(ctx, f"{msg}\n{table.table}")
        else:
            msg += f"```{table.table}```"
            await ctx.send(msg)


@bot.command(
    name="rate",
    help=f"rate a given challenge on a scale of {SETTINGS['rating_min']} to {SETTINGS['rating_max']}",
)
async def rate(ctx, chall_id: int, user_rating: int):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx,
        msg=f"Hey, <@{ctx.author.id}>, don't submit a challenge in public channels...",
    ):
        return

    with db.db_session:
        chall = db.Challenge.get(id=chall_id)
        user = db.User.get(name=username(ctx))

        # percentComplete does account your teammates.
        if db.percentComplete(chall, user) == 0:
            await ctx.send(
                "You can only rate a challenge if you or someone on your team has captured at least 1 flag for it..."
            )
            return

        user_rating = db.rate(user, chall, user_rating)

    if user_rating == -1:
        await ctx.send("Invalid challenge or challenge not unlocked...")
        return
    else:
        await ctx.send(f"You rated challenge ID `{chall_id}` a `{user_rating}`.")


@bot.command(
    name="byoc_stats",
    help="this will show you stats about the BYOC challenges you've created. total profit from solves, etc.",
    aliases=["bstats", "bstat"],
)
async def byoc_stats(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx,
        msg=f"Hey, <@{ctx.author.id}>, don't submit a challenge in public channels...",
    ):
        return

    msg = ""
    with db.db_session:
        user = db.User.get(name=username(ctx))
        team_challs = list(
            db.select(c for c in db.Challenge if c.author in db.getTeammates(user))  # type: ignore
        )

        # num solves per challenge
        stats = list()
        for chall in team_challs:
            num_solves = list(db.select(s for s in db.Solve if s.challenge == chall))  # type: ignore

            chall_rewards = sum(
                db.select(  # type: ignore
                    sum(t.value)
                    for t in db.Transaction  # type: ignore
                    if t.type == "byoc reward"
                    and t.recipient in db.getTeammates(user)
                    and t.challenge == chall
                ).without_distinct()
            )

            line = [
                chall.id,
                chall.title,
                len(num_solves),
                chall.author.name,
                chall_rewards,
            ]

            stats.append(line)
        stats.insert(0, ["Chall ID", "Title", "# Solves", "Author", "Payout"])

        table = GithubFlavoredMarkdownTable(stats)

        # team total byoc rewards sum
        total_byoc_rewards = sum(
            db.select(  # type: ignore
                sum(t.value)
                for t in db.Transaction  # type: ignore
                if t.type == "byoc reward" and t.recipient in db.getTeammates(user)
            )
        )

    await ctx.send(
        f"Your stats ```{table.table}```\n**Team Total BYOC Rewards:** `{total_byoc_rewards}` points"
    )


async def loadBYOCFile(ctx):
    if len(ctx.message.attachments) != 1:
        await ctx.send("You didn't attach the challenge file...")
        return {}

    raw = await ctx.message.attachments[0].read()
    raw = raw.decode()

    fname = ctx.message.attachments[0].filename

    # Do I want to support as many formats as possible?
    # keep json, add toml, add yaml

    # how do I distinguish between toml and json and yaml?

    if ".json" in fname.lower():
        try:
            challenge_object = json.loads(
                raw
            )  # how do we get the challenge object loaded?
            return challenge_object
        except json.JSONDecodeError as e:
            await ctx.send("Error decoding json. check syntax ")
    elif ".toml" in fname.lower():
        try:
            challenge_object = toml.loads(
                raw
            )  # how do we get the challenge object loaded?
            return challenge_object
        except toml.TomlDecodeError as e:
            await ctx.send("Error decoding toml. check syntax ")
    else:
        await ctx.send(
            "Unsupported file type... make sure the extensions are json or toml"
        )

    return {}


@bot.command(
    name="byoc_ext",
    help="this is how you will submit BYOC challenges that are externally validated.",
    aliases=["esub"],
)
@commands.cooldown(
    1, SETTINGS["_rate_limit_window"], type=discord.ext.commands.BucketType.user
)  # one submission per second per user
async def byoc_ext(
    ctx: discord.ext.commands.Context, chall_id: int, submitted_flag: str
):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't submit flags in public channels..."
    ):
        return

    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return

    if SETTINGS["_debug"] == True and SETTINGS["_debug_level"] == 1:
        logger.debug(
            f"{username(ctx)} is attempting to submit '{submitted_flag}' to external chall ID {chall_id}"
        )

    with db.db_session:
        # is this a valid challenge
        chall = db.Challenge.get(id=chall_id)
        user = db.User.get(name=username(ctx))
        if chall == None or user == None:
            msg = f"Challenge id {chall_id} not found... you likely forgot to add it."
            if SETTINGS["_debug"]:
                logger.debug(msg)
            await ctx.send(msg)
            return

        res = db.createExtSolve(user, chall, submitted_flag)
        if res == 1337:
            await ctx.send(f"Correct! Your score is now `{db.getScore(user)}`")
            return

        await ctx.send(
            f"External validation server reported that your flag was incorrect... talk to <@{(await getDiscordUser(ctx,chall.author.name)).id}>: {res}"
        )


@bot.command(
    name="byoc_check",
    help="this will check your BYOC challenge is valid. It will show you how much it will cost to post",
    aliases=["bcheck"],
)
@commands.cooldown(
    1, SETTINGS["_rate_limit_window"], type=discord.ext.commands.BucketType.user
)  # one submission per second per user
async def byoc_check(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx,
        msg=f"Hey, <@{ctx.author.id}>, don't check a challenge in public channels...",
    ):
        return

    challenge_object = await loadBYOCFile(ctx)

    challenge_object["author"] = username(ctx)

    if SETTINGS["_debug"] and SETTINGS["_debug_level"] == 2:
        logger.debug(f"checking challenge:  {challenge_object}")

    result = db.validateChallenge(challenge_object)

    if result["valid"] == True:
        msg = renderChallenge(result, preview=True)
        await sendBigMessage(ctx, msg, wrap=False)
    else:
        await ctx.send(
            f"challenge invalid. Ensure that all required fields are present. see `example_challenge.toml` \n\nfail_reason:{result['fail_reason']}"
        )


@bot.command(
    name="byoc_commit",
    help="this will commit your BYOC challege. You will be charged a fee and will have to confirm the submission",
    aliases=["bcommit"],
)
@commands.cooldown(
    1, SETTINGS["_rate_limit_window"], type=discord.ext.commands.BucketType.user
)  # one submission per second per user
async def byoc_commit(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx,
        msg=f"Hey, <@{ctx.author.id}>, don't submit a challenge in public channels...",
    ):
        return

    if ctfRunning() == False:
        await ctx.send("CTF isn't running yet")
        return

    # print(dir(ctx.bot))
    # exit()
    challenge_object = await loadBYOCFile(ctx)
    challenge_object["author"] = username(
        ctx
    )  # this should prevent someone from submitting a challenge as someone else... sneaky... lol
    result = db.validateChallenge(challenge_object)
    channel = ctx.channel

    def check(msg):
        return msg.content == "confirm" and msg.channel == channel
        # TODO  https://discordpy.readthedocs.io/en/latest/api.html#discord.Client.wait_for

    if result["valid"] == False:
        await ctx.send(
            f"challenge invalid. Ensure that all required fields are present. see example_challenge.toml\n\nfail_reason:{result['fail_reason']}"
        )
        return

    chall_preview = renderChallenge(result, preview=True)

    await sendBigMessage(ctx, chall_preview, wrap=False)
    await ctx.send(
        "\n\n\n***Reply with `confirm` in the next 20 seconds to pay for and publish your challenge.***"
    )
    resp = None
    try:
        resp = await ctx.bot.wait_for("message", check=check, timeout=20)
    except asyncio.exceptions.TimeoutError as e:
        await ctx.send("**Cancelling...**")
        return
    if resp.content == "confirm":
        chall_id = db.buildChallenge(result, byoc=True)
        if chall_id == -1:
            if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
                logger.debug(f"{username(ctx)} had insufficient funds.")
            await ctx.send("Insufficient funds...")
            return
        if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
            logger.debug(f"{username(ctx)} created  chall id {chall_id}")

        # alert others via the ctf channel
        ctf_chan = bot.get_channel(SETTINGS["_ctf_channel_id"])
        user = await getDiscordUser(ctx, username(ctx))
        await ctf_chan.send(
            f"New BYOC challenge from <@{user.id}>. \n`{result['challenge_title']}` for `{result['value']}` points\nUse `!view {chall_id}` to see it"
        )
        await ctx.send(
            f"Challenge Accepted! Use `!view {chall_id}` to see it and `!byoc_stats` to see who has solved it."
        )
        return

    await ctx.send("**Cancelling...**")
    return


@bot.command("tutorial", help="a tldr for essential commands", aliases=["tut"])
async def tutorial(ctx):
    # if await inPublicChannel(ctx, msg=f"Hey, <@{ctx.author.id}>, don't view the tutorial in public channels..."):
    #     return

    byoctf_chan = bot.get_channel(SETTINGS["_ctf_channel_id"])
    msg = f"""
**How to play**

Try to keep your "public" interactions (tips mainly) in the {byoctf_chan.mention} channel. 

Only communicate with <@{bot.user.id}> via direct messages (User ID:{bot.user.id}) 

Key commands 
- `!reg <team_name> <team_password>` - register and join *teamname*; super case-sensitive.  
  -- wrap in quotes if you have spaces in the teamname; 
  -- if the team exists and your password is correct, you're in. 
  -- if no team exists with the name specified, the team will be created with password specified. 
  -- leading and trailing spaces are stripped from team name and password.
- `!top` - shows your score 
- `!all [tag]` - filter challenges by tag; use !tag to exclude
- `!v <challenge_id>` - detail view of a specific challenge
- `!sub <flag>` - submit a flag you find while working on a challenge
- `!esub <chall_id> <flag>` - submit an externally validated flag. (challenge should say if it's externally validated.)
- `!solves` - show all the flags your team has submitted. 
- `!unsolved` - show all of the unlocked challenges that don't have at least one submission. 
- `!rate <challenge_id> <val>` - rate a challenge on a scale (`Currently {SETTINGS['rating_min']}-{SETTINGS['rating_max']}`). if others say it's garbage, don't waste your time... you can only rate if you capture at least one of the flags for the challenge. 
- `!log` - all transactions you particpated in (sender or recipient of a tip, BYOC rewards and fees, and solves among other things)
- `!pub` - all transactions that have happened the game. if scoreboard is private, amounts are omitted. 
- `!psol [challenge_id]` - all solves for all challenges or just challenge_id 
- `!help` - shows the long name of all of the commands. Most of the above commands are aliases or shorthand for a longer command.
"""

    await sendBigMessage(ctx, msg, wrap=False)


@bot.command(
    "public_solves",
    help="show who solved challenges for all challenges (sans sensitive info)",
    aliases=["psol", "psolves"],
)
async def public_solves(ctx, chall_id: int = 0):
    if await isRegistered(ctx) == False:
        return
    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't dump logs public channels..."
    ):
        return

    with db.db_session:
        if chall_id > 0:
            if SETTINGS["scoreboard"] == "public":
                logs = list(
                    db.select(  # type: ignore
                        (
                            t.recipient.team.name,
                            t.recipient.name,
                            t.challenge.title,
                            t.value,
                            t.time,
                        )
                        for t in db.Transaction
                        if t.type == "solve" and t.challenge.id == chall_id
                    )  # type: ignore
                )
                logs.insert(0, ["Team", "Recipient", "Challenge", "Amount", "Time"])
            else:
                logs = list(
                    db.select(  # type: ignore
                        (
                            t.recipient.team.name,
                            t.recipient.name,
                            t.challenge.name,
                            t.time,
                        )
                        for t in db.Transaction
                        if t.type == "solve" and t.challenge.id == chall_id
                    )  # type: ignore
                )
                logs.insert(0, ["Team", "Recipient", "Challenge", "Time"])
        else:
            if SETTINGS["scoreboard"] == "public":
                logs = list(
                    db.select(  # type: ignore
                        (
                            t.recipient.team.name,
                            t.recipient.name,
                            t.challenge.title,
                            t.value,
                            t.time,
                        )
                        for t in db.Transaction
                        if t.type == "solve"
                    )  # type: ignore
                )
                logs.insert(0, ["Team", "Recipient", "Challenge", "Amount", "Time"])
            else:
                logs = list(
                    db.select(  # type: ignore
                        (
                            t.recipient.team.name,
                            t.recipient.name,
                            t.challenge.name,
                            t.time,
                        )
                        for t in db.Transaction
                        if t.type == "solve"
                    )  # type: ignore
                )
                logs.insert(0, ["Team", "Recipient", "Challenge", "Time"])

    table = GithubFlavoredMarkdownTable(logs)
    await sendBigMessage(
        ctx, f"Public Log of Solves for all challenges:\n\n{table.table}"
    )


@bot.command(
    "public_log",
    help="list of all transactions (sans sensitive info)",
    aliases=["plog", "pub", "ledger", "led"],
)
async def public_log(ctx):
    if await isRegistered(ctx) == False:
        return

    if await inPublicChannel(
        ctx, msg=f"Hey, <@{ctx.author.id}>, don't dump logs public channels..."
    ):
        return
    with db.db_session:
        if SETTINGS["scoreboard"] == "public":
            logs = list(
                db.select(  # type: ignore
                    (t.sender.name, t.recipient.name, t.type, t.value, t.time)
                    for t in db.Transaction  # type: ignore
                )
            )
            logs.insert(0, ["Sender", "Recipient", "Type", "Amount", "Time"])
        else:
            logs = list(
                db.select(  # type: ignore
                    (t.sender.name, t.recipient.name, t.type, t.time)
                    for t in db.Transaction  # type: ignore
                )
            )
            logs.insert(0, ["Sender", "Recipient", "Type", "Time"])

    table = GithubFlavoredMarkdownTable(logs)
    await sendBigMessage(ctx, f"Public Log of Transactions:\n\n{table.table}")


if __name__ == "__main__":
    banner()
    try:
        from custom_secrets import DISCORD_TOKEN
    except ImportError:
        print("Failure to import DISCORD_TOKEN from secrets.py")
        exit()
    bot.run(DISCORD_TOKEN)
