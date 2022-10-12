from collections import Counter
import hashlib

from requests.sessions import session
from settings import SETTINGS
import json
import toml

import requests

from loguru import logger

logger.add(SETTINGS.get("_logfile"))

from datetime import datetime
from pony.orm import *

# https://editor.ponyorm.com/user/shyft/byoctf/designer
# this is probably a bit of an overcomplicated db architecture.
# this is because I was learning the relationships and how they worked in pony.
# things also changed in the project and I left some things in order to not break stuff.

db = Database()


class Flag(db.Entity):
    id = PrimaryKey(int, auto=True)
    challenges = Set("Challenge")
    description = Optional(str)
    solves = Set("Solve")
    flag = Required(str)
    value = Required(float)
    unsolved = Optional(bool, default=True)
    bonus = Optional(bool, default=False)
    tags = Set("Tag")
    author = Required("User")
    byoc = Optional(bool)
    transaction = Optional("Transaction")
    reward_capped = Optional(bool, default=False)


class Challenge(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    flags = Set(Flag)
    author = Required("User")
    description = Optional(str)
    parent = Set("Challenge", reverse="children")
    children = Set("Challenge", reverse="parent")
    tags = Set("Tag")
    release_time = Optional(datetime, default=lambda: datetime.now())
    visible = Optional(bool, default=True)
    hints = Set("Hint")
    byoc = Optional(bool, default=False)
    byoc_ext_url = Optional(str, nullable=True, default=None)
    unsolved = Optional(bool, default=True)
    byoc_ext_value = Optional(float)
    solve = Set("Solve")
    transaction = Set("Transaction")
    ratings = Set("Rating")


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    challenges = Set(Challenge)
    solves = Set("Solve")
    team = Optional("Team")
    sent_transactions = Set("Transaction", reverse="sender")
    recipient_transactions = Set("Transaction", reverse="recipient")
    authored_flags = Set(Flag)
    ratings = Set("Rating")


class Solve(db.Entity):
    id = PrimaryKey(int, auto=True)
    time = Optional(datetime, default=lambda: datetime.now())
    flag = Optional(Flag)
    user = Required(User)
    value = Required(float)
    transaction = Optional("Transaction")
    challenge = Optional(Challenge)
    flag_text = Optional(str)


class Team(db.Entity):
    id = PrimaryKey(int, auto=True)
    members = Set(User)
    name = Required(str)
    password = Required(str)


class Tag(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    challenges = Set(Challenge)
    flags = Set(Flag)


class Transaction(db.Entity):
    id = PrimaryKey(int, auto=True)
    value = Optional(float)
    sender = Required(User, reverse="sent_transactions")
    recipient = Required(User, reverse="recipient_transactions")
    type = Required(str)
    message = Optional(str)
    time = Optional(datetime, default=lambda: datetime.now())
    solve = Optional(Solve)
    hint = Optional("Hint")
    flag = Optional(Flag)
    challenge = Optional(Challenge)


class Hint(db.Entity):
    id = PrimaryKey(int, auto=True)
    text = Required(str)
    cost = Optional(float)
    challenge = Required(Challenge)
    transaction = Optional(Transaction)


class Rating(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    challenge = Required(Challenge)
    value = Optional(int, default=0)  # 1-5


#########


def seedDB():
    # ensure the built in accounts for bot an botteam exist; remove from populateTestdata.py
    with db_session:
        unaffiliated = db.Team.get(name="__unaffiliated__")
        if unaffiliated == None:
            unaffiliated = db.Team(name="__unaffiliated__", password="__unaffiliated__")

        botteam = db.Team.get(name="__botteam__")
        if botteam == None:
            botteam = db.Team(name="__botteam__", password="__botteam__")

        bot = db.User.get(id=0)
        if bot == None:
            bot = db.User(id=0, name=SETTINGS["_botusername"], team=botteam)

        commit()


def generateMapping():
    # https://docs.ponyorm.org/database.html
    if SETTINGS["_db_type"] == "sqlite":
        db.bind(provider="sqlite", filename=SETTINGS["_db_database"], create_db=True)
    elif SETTINGS["_db_type"] == "postgres":
        print("postgres is untested... good luck...")
        db.bind(
            provider="postgres",
            user=SETTINGS["_db_user"],
            password=SETTINGS["_db_pass"],
            host=SETTINGS["_db_host"],
            database=SETTINGS["_db_database"],
        )
    elif SETTINGS["_db_type"] == "mysql":
        print("mysql is untested... good luck...")
        db.bind(
            provider="mysql",
            user=SETTINGS["_db_user"],
            password=SETTINGS["_db_pass"],
            host=SETTINGS["_db_host"],
            database=SETTINGS["_db_database"],
        )

    # db.create_tables()
    db.generate_mapping(create_tables=True)


generateMapping()


@db_session
def showTeams():
    pass


@db_session
def getTeammates(user):
    """this includes the user in the list of teammates..."""
    res = list(select(member for member in User if member.team.name == user.team.name))
    return res


@db_session
def getScore(user):
    if type(user) == str:  # for use via cmdline in ctrl_ctf.py
        # logger.debug(f'looking for user {user}')
        user = User.get(name=user)
        if user == None:
            return "User is None... "
    # https://docs.ponyorm.org/queries.html#automatic-distinct
    # hence the without_distint()
    received = sum(
        select(t.value for t in Transaction if t.recipient == user).without_distinct()
    )
    sent = sum(
        select(t.value for t in Transaction if t.sender == user).without_distinct()
    )
    if SETTINGS["_debug"] == True and SETTINGS["_debug_level"] > 1:
        logger.debug(
            f"{user.name} has received {received}, - sent {sent} = {received - sent}"
        )

    return received - sent


@db_session
def getTeammateScores(user):
    teammates = list(
        select(member for member in User if member.team.name == user.team.name)
    )
    res = [(tm.name, getScore(tm)) for tm in teammates]
    return res


@db_session
def challValue(challenge: Challenge):
    if challenge.byoc_ext_value != None:
        return challenge.byoc_ext_value

    if challenge.id == 0:
        return 0

    flags = list(select(c.flags for c in Challenge if c.id == challenge.id))
    # if SETTINGS['_debug']:
    if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
        logger.debug(f"flags{flags}")
    val = sum([flag.value for flag in flags])
    # logger.debug(f'challenge {challenge.title} is worth {val} points')
    return val


@db_session()
def topPlayers(num=10):
    all_users = select(u for u in User if u.name != SETTINGS["_botusername"])

    topN = [(u, getScore(u)) for u in all_users]
    if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
        logger.debug(f"topN: {topN}")

    if len(topN) > num:
        return sorted(topN, key=lambda x: x[1], reverse=True)[:num]
    else:
        return sorted(topN, key=lambda x: x[1], reverse=True)


@db_session()
def getTopTeams(num=3):
    all_users = select(u for u in User if u.name != SETTINGS["_botusername"])

    all_scores = [(u, getScore(u)) for u in all_users]
    # logger.debug(f'all_scores: {all_scores}')

    scores = {}
    for user, score in all_scores:
        scores[user.team.name] = scores.get(user.team.name, 0) + score

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if num <= len(sorted_scores):
        res = sorted_scores[:num]
    else:
        res = sorted_scores
    if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
        logger.debug(f"sorted scores: {res}")
    return res


@db_session()
def challegeUnlocked(user, chall):
    """returns true if all the dependencies for a given challenge have been met by the specified user"""
    # logger.debug(f'{user.name} wants to access {chall.title}')

    # get all solves for this user and their teammates.

    teammates = getTeammates(user)  # including self
    # logger.debug(f'players {[x.name for x in teammates]}')
    # logger.debug(user.team.name)
    team_solves = []
    for teammate in teammates:
        team_solves += list(
            select(solve.flag for solve in Solve if teammate.name == solve.user.name)
        )
    # logger.debug(f'team_solves {team_solves}')

    # logger.debug(f'"{chall.title}" has a parent "{chall.parent.name}" challenge dependencies {chall.children}')

    parent_flags = list(chall.parent.flags)

    got_all_flags = all(flag in team_solves for flag in parent_flags)
    if SETTINGS["_debug"] and SETTINGS["_debug_level"] == 2:
        logger.debug(f"team_solves: {team_solves}")
        logger.debug(f"parent_flags: {parent_flags}")
        logger.debug(f"got_all_flags { got_all_flags}")

    if got_all_flags == True:
        return True
    return False


@db_session()
def rate(user, chall, user_rating):
    if chall == None or challegeUnlocked(user, chall) == False:
        return -1

    # is the rating within the bounds
    if user_rating < SETTINGS["rating_min"]:
        user_rating = SETTINGS["rating_min"]
    elif user_rating > SETTINGS["rating_max"]:
        user_rating = SETTINGS["rating_max"]

    prev_rating = Rating.get(user=user, challenge=chall)
    if prev_rating:
        # update your previous rating
        prev_rating.value = user_rating
    else:
        new_rating = Rating(user=user, challenge=chall, value=user_rating)

    return user_rating


@db_session()
def get_all_challenges(user: User):
    # show only challenges which are not hidden (dependencies resolved and released)

    raw = list(select(c for c in Challenge if c.visible == True))

    challs = [c for c in raw if challegeUnlocked(user, c)]
    # logger.debug(f'indb: {[(x.title, [y for y in x.flags]) for x in challs]}')

    return challs


@db_session()
def get_unsolved_challenges(user: User):
    # show only challenges which are not hidden AND unsolved by a user

    # raw = list(select(c for c in Challenge if c.visible == True ) )

    # challs = [c for c in raw if challegeAvailable(user, c) ]
    # logger.debug(challs)

    raw = list(select(c for c in Challenge if c.visible == True))

    challs = [c for c in raw if challegeUnlocked(user, c)]

    ret = []
    for chall in challs:
        if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
            logger.debug("flags", list(chall.flags))
        for flag in list(chall.flags):
            # solve = Solve.get(user=user, flag=flag.flag)
            solves = list(
                select(
                    s
                    for s in Solve
                    if s.user.id == user.id and s.flag.flag == flag.flag
                )
            )
            if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 1:
                logger.debug(solves)
            if len(solves) == 0:
                ret.append(chall)
    return ret


@db_session()
def getMostCommonFlagSolves(num=3):
    solves = Counter(select(solve.flag for solve in Solve))

    if SETTINGS["_debug"] and SETTINGS["_debug_level"] > 2:
        logger.debug(solves)

    # for solve
    return solves.most_common(num)


@db_session
def getHintTransactions(user: User):
    res = select(
        t for t in Transaction if t.sender.name == user.name and t.type == "hint buy"
    )[:]
    return res


@db_session
def buyHint(user: User = None, challenge_id: int = 0):
    # this is to abstract away some of the issues with populating test data
    # see around line 400 in buy_hint in byoctf_discord.py

    # does challenge have hints
    chall = Challenge.get(id=challenge_id)
    if chall.author in getTeammates(user):
        return "You shouldn't have to buy your own hints...", None

    chall_hints = list(chall.hints)
    if SETTINGS["_debug"]:
        logger.debug(
            f"Trying to buy hint for challenge_id {challenge_id} and user {user.name}"
        )
    # has user purchased these hints
    hint_transactions = []
    hints_to_buy = []
    teammates = getTeammates(user)
    for hint in chall_hints:
        hint_transaction = select(
            t for t in Transaction if t.sender in teammates and t.hint == hint
        ).first()
        # print(hint_transaction)

        if (
            hint_transaction != None
        ):  # a purchase exists (not None); no need to buy it again
            continue  # so try the next hint in the list of challenge hints
        else:
            hints_to_buy.append(hint)

    if len(hints_to_buy) < 1:
        if SETTINGS["_debug"] == True and SETTINGS["_debug_level"] > 0:
            logger.debug(
                f"{user.name} has no more hints for challenge id {challenge_id}"
            )
        return "There are no more hints available to purchase for this challenge.", None

    # print(f'hint transactions: {hint_transactions}')
    # print(f'hints available to purchase {hints_to_buy}')
    sorted_hints = sorted(hints_to_buy, key=lambda x: x.cost, reverse=False)

    # does user have enough funds
    funds = getScore(user)
    if funds >= sorted_hints[0].cost:
        botuser = User.get(name=SETTINGS["_botusername"])
        cheapest_hint = sorted_hints[0]
        hint_buy = Transaction(
            sender=user,
            recipient=botuser,
            hint=cheapest_hint,
            value=cheapest_hint.cost,
            type="hint buy",
            message=f"bought hint for challengeID {challenge_id}",
        )

        if (
            "byoc" in [t.name for t in chall.tags]
            and SETTINGS["_byoc_hint_reward_rate"] > 0
        ):
            botuser = db.User.get(id=0)
            reward = cheapest_hint.cost * SETTINGS["_byoc_hint_reward_rate"]
            byoc_hint = Transaction(
                sender=botuser,
                recipient=chall.author,
                value=reward,
                type="byoc hint reward",
                message=f"hint buy from {user.name}",
                challenge=chall,
                hint=cheapest_hint,
            )
        return "ok", cheapest_hint
    return "insufficient funds", None


@db_session
def createExtSolve(user: User, chall: Challenge, submitted_flag: str):
    if chall.byoc_ext_url == None:
        msg = f"Challenge id {chall.id} is not an externally validated challenge."
        if SETTINGS["_debug"]:
            logger.debug(msg)
        return msg

    if user in getTeammates(chall.author):
        msg = f"You can't submit a challenge from a teammate or yourself... "
        if SETTINGS["_debug"]:
            logger.debug(msg)
        return msg

    payload = {"challenge_id": chall.id, "flag": submitted_flag, "user": user.name}

    resp = requests.post(chall.byoc_ext_url, data=payload)
    # breakpoint()

    if resp.status_code != 200:
        msg = f"Challenge id {chall.id} external validation server isn't responding correctly. talk to the author..."
        if SETTINGS["_debug"]:
            logger.debug(msg)
        return msg

    data = json.loads(resp.text)

    if data.get("msg") == "correct":
        botuser = User.get(name=SETTINGS["_botusername"])
        reward = chall.byoc_ext_value

        # first blood
        if chall.unsolved == True:
            reward += chall.byoc_ext_value * (SETTINGS["_firstblood_rate"])
            chall.unsolved = False

            if SETTINGS["_debug"] == True:
                logmsg = f"First blood solve for {user.name} #{chall.id}{chall.title} base_value={chall.byoc_ext_value} reward={reward}"

        hashed_flag = hashlib.sha256(
            submitted_flag.encode()
        ).hexdigest()  # fixes us being able to see flags for ext solves.
        solve = Solve(value=reward, user=user, challenge=chall, flag_text=hashed_flag)

        solve_credit = Transaction(
            sender=botuser,
            recipient=user,
            value=reward,
            type="ext_solve",
            message=f"esub {chall.id}; sha256-{hashed_flag}",
            solve=solve,
            challenge=chall,
        )
        flag: Flag
        for flag in chall.flags:
            if flag.reward_capped == True:
                logger.debug(
                    f"reward capped (possibly for abuse) for flag {flag.flag} by {flag.author.name}. No BYOC points will be awarded to challenge author for this solve"
                )
                return

        # reward for author
        reward = chall.byoc_ext_value * SETTINGS["_byoc_reward_rate"]

        msg = f"byoc reward: {user.name} of {user.team.name} submitted external flag for {chall.title}: sha256 {hashed_flag}"
        if SETTINGS["_debug"] == True:
            logger.debug(f"{chall.author.name} got {msg}")

        author_reward = Transaction(
            recipient=chall.author,
            sender=botuser,
            value=reward,
            type="byoc reward",
            message=msg,
        )

        commit()
        return 1337
    return "not 1337"


@db_session
def createSolve(
    user: User = None, flag: Flag = None, msg: str = "", challenge: Challenge = None
):
    botuser = User.get(name=SETTINGS["_botusername"])

    if challenge == None:
        challenge = select(c for c in Challenge if flag in c.flags).first()
        if challenge == None:  # it's still not found...
            challenge = Challenge.get(title="__bonus__")

    if SETTINGS["_debug"]:
        # print(type)
        logger.debug(
            f"{user.name} is solving for {flag.flag}; part of challenge {challenge.title}."
        )

    if SETTINGS["_debug"] == True:
        # logger.debug(f'user {user}; flag {flag.flag}; challenge {challenge}')
        logmsg = ""

    if flag != None:
        team = getTeammates(user)
        # print('team', [x.name for x in team])
        previousSolve = select(
            s for s in Solve if s.user in team and s.flag_text == flag.flag
        ).first()

        if previousSolve != None:
            if SETTINGS["_debug"] == True:
                logger.debug(
                    f"{flag.flag} already submitted by {previousSolve.user.name}"
                )
            return

        team = getTeammates(user)
        if flag.author in team or challenge.author in team:
            if SETTINGS["_debug"] == True:
                logger.debug(
                    f"{user.name} is trying to submit their own flag or a flag authored teammate. (flag by {flag.author.name}) OR is a part of a challenge authored by someone on the team. (chall by {challenge.author.name})"
                )
            return

    value = 0
    if flag != None:
        value = flag.value
    elif challenge != None:
        value = challenge.byoc_ext_value

    if value == 0:
        logger.debug(
            "neither challenge or flag have a value other than None... investigate via breakpoint() "
        )
        # breakpoint()
        return

    reward = value

    # this is where we can implement different flag types
    # FIFO
    #   only one team can capture this flag
    #   no other team can get points for a solve...
    #   it won't be known if this has been solved but it should be clear if this challenge is of that type?
    # Pool
    #   teams that solve this flag split the total pot
    #   ex : total points 3000
    #   3 of 20 teams solve the challenge
    #        each team gets 1000 points
    #   4 of 20 teams solve the challenge
    #        each team gets 750 points
    # Mystery
    #   points awarded unknown until the end of the game
    #   could be linked to number of solves or rating or simply hidden?
    #
    # if flag.type == 'FIFO':
    #     reward = flag.value
    #     challenge.visible = False # disable the challenge so noone else can see it?

    # this becomes part of a big elif chain
    if flag.unsolved == True:
        reward += value * (SETTINGS["_firstblood_rate"])
        flag.unsolved = False

        if SETTINGS["_debug"] == True:
            logmsg = f"First blood solve for {user.name} {flag.flag} base_value={value} reward={reward}"

    # this is hard to think about with the external validation...
    if SETTINGS["_decay_solves"] == True:
        solve_count = count(
            select(
                t for t in Transaction if t.solve.flag_text == flag.flag
            ).without_distinct()
        )

        team_count = count(select(t for t in Team)) - 1  # don't count discordbot's team

        solve_percent = solve_count / team_count

        reward *= max(
            [1 - solve_percent, SETTINGS["_decay_minimum"]]
        )  # don't go below minimum

        logmsg = f"{solve_count} teams ({solve_percent * 100}%) have solved {flag.flag}; The reward is {reward}"

        if SETTINGS["_debug"] == True:
            logger.debug(logmsg)

    #
    if msg == "" and flag != None:
        msg = f"{flag.flag} is part of: " + "\n".join(
            [c.title for c in flag.challenges]
        )

    solve = Solve(
        value=reward, user=user, challenge=challenge, flag=flag, flag_text=flag.flag
    )
    # breakpoint()
    solve_credit = db.Transaction(
        sender=botuser,
        recipient=user,
        value=reward,
        type="solve",
        message=msg,
        solve=solve,
        challenge=challenge,
        flag=flag,
    )

    commit()

    if flag.reward_capped == True:
        logger.debug(
            f"reward capped (possibly for abuse) for flag {flag.flag} by {flag.author.name}. No BYOC points will be awarded to challenge author for this solve"
        )
        return

    if flag.byoc == True:
        reward = value * SETTINGS["_byoc_reward_rate"]
        if SETTINGS["_debug"] == True:
            logger.debug(
                f"byoc reward of {reward} sent to {flag.author.name}: {user.name} of {user.team.name} submitted {flag.flag}"
            )
        author_reward = db.Transaction(
            recipient=flag.author,
            sender=botuser,
            value=reward,
            type="byoc reward",
            message=f"{user.name} of {user.team.name} submitted {flag.flag} for challenge {challenge.title}",
            challenge=challenge,
        )
        # print(f'{challenge}')

    elif challenge.byoc == True:
        reward = value * SETTINGS["_byoc_reward_rate"]
        author_reward = db.Transaction(
            recipient=flag.author,
            sender=botuser,
            value=reward,
            type="byoc reward",
            message=f"{user.name} of {user.team.name} submitted an external flag",
            challenge=challenge,
        )

        if SETTINGS["_debug"] == True:
            logger.debug(
                f"byoc reward of {reward} sent to {challenge.author.name}: {user.name} of {user.team.name} submitted an external flag."
            )

    commit()

    if SETTINGS["_debug"] and SETTINGS["_debug_level"] >= 1:
        logger.debug(f"{solve.user.name} solved {solve.flag_text}")


# @db_session
# def decayCalc(challenge:Challenge):
#     pass


@db_session
def percentComplete(chall: Challenge, user: User):
    try:
        flags = list(chall.flags)
    except AttributeError as e:
        return 0
    num_solves_for_chall = 0
    teammates = getTeammates(user)  # look for all solves from my team. not just me.
    for flag in flags:
        for teammate in teammates:
            if Solve.get(user=teammate, flag_text=flag.flag):
                num_solves_for_chall += 1
    try:
        return (num_solves_for_chall / len(flags)) * 100
    except ZeroDivisionError as e:
        # the len() of flags is zero... challenge without flags...
        return 0


@db_session
def challengeComplete(chall: Challenge, user: User):
    if percentComplete(chall, user) == 100:
        return True
    return False


@db_session()
def validateChallenge(challenge_object):
    if SETTINGS["_debug"]:
        logger.debug(f"validating the challenge from {challenge_object.get('author')}")
        if SETTINGS["_debug_level"] >= 1:
            logger.debug(f"Got challenge object: { challenge_object}")

    result = {
        "valid": False,
        "author": challenge_object.get("author"),
        "tags": [],
        "challenge_title": "",
        "challenge_description": "",
        "parent_ids": [],
        "flags": [],
        "hints": [],
        "value": 0,  # sum of flags
        "cost": 0,
        "fail_reason": "",
        "external_validation": False,
        "byoc": True,
    }

    # does the challenge_object have all of the fields we need?
    # title, description, tags, flags with at least one flag, hints

    # title
    if (
        type(challenge_object.get("challenge_title")) == None
        or len(challenge_object.get("challenge_title", "")) < 1
    ):
        result["fail_reason"] += "; title too short or non-existent"
        return result

    c = Challenge.get(title=challenge_object.get("challenge_title"))
    if c:
        result["fail_reason"] += "; failed title uniqueness"
        return result

    result["challenge_title"] = challenge_object["challenge_title"]

    if type(challenge_object.get("challenge_description")) == None or (
        len(challenge_object.get("challenge_description", "")) < 1
        or len(challenge_object.get("challenge_description", "")) > 1500
    ):

        result["fail_reason"] += "; failed description length (too long or too short?) "
        return result
    result["challenge_description"] = challenge_object["challenge_description"]

    # check that at least one tag exists
    if len(challenge_object["tags"]) < 1:
        result["fail_reason"] += "; failed tags exist (mispelled?)"
        return result
    for tag in challenge_object["tags"]:
        if type(tag) == str and len(tag) < 1:
            result["fail_reason"] += "; failed tag name length"
            return result
    result["tags"] = challenge_object["tags"]

    # check the hints.
    for hint in challenge_object.get("hints", []):
        if hint.get("hint_cost") < 0:
            result["fail_reason"] += "; failed hint cost value (less than 0)"
            return result
        if len(hint.get("hint_text")) < 1:
            result["fail_reason"] += "; failed hint text length"
            return result

    result["hints"] = challenge_object["hints"]

    # is it externally validated?
    if challenge_object.get("external_validation") == True:
        # can we reach the endpoint via requests?
        try:
            resp = requests.get(challenge_object.get("external_validation_url"))
            data = json.loads(resp.text)

        except BaseException as e:
            result["fail_reason"] += f"; failed validate http request to ext url ({e})"
            return result

        result["external_validation_url"] = challenge_object["external_validation_url"]

        if challenge_object.get("external_challenge_value", 0) < 100:
            result["fail_reason"] += "; failed external challenge value"
            return result

        result["value"] = challenge_object.get("external_challenge_value")

    else:  # it's not externally validated so...
        # check the flags
        for flag in challenge_object["flags"]:
            # Are the flags unique? not likely to occur, but needs to be checked. this has the potential to leak info about flags that exist. Just make sure they are decent flags. Might just have to accept this risk
            try:
                res = Flag.get(flag=flag.get("flag_flag"))
            except BaseException as e:
                return result
            if res:
                result["fail_reason"] += "; failed flag uniqueness"
                return result

            # collect all of the flags from the obj and sum the value then display the cost to post challenge to the user.
            if flag.get("flag_value", -1) < 0:
                result[
                    "fail_reason"
                ] += "; failed flag individual value (missing or less than 0)"
                return result
            result["value"] += flag.get("flag_value")

        # flags aren't worth enough... 100 point minimum
        if result["value"] < SETTINGS["_byoc_chall_min_val"]:
            result["fail_reason"] += "; failed flag cumulative value"
            return result

        result["flags"] = challenge_object["flags"]

    # parent challenges
    parents = challenge_object.get("depends_on", [])
    for parent_id in parents:
        try:
            parent_id = int(parent_id)
        except:
            result[
                "fail_reason"
            ] += f"; invalid parent challenge ID {parent_id}; should be an integer "
            if SETTINGS["_debug"] and SETTINGS["_debug_level"] >= 1:
                logger.debug(result["fail_reason"])
            return result
        parent = Challenge.get(id=parent_id)
        if parent == None:
            result[
                "fail_reason"
            ] += f"; parent challenge ID {parent_id} does not exist (it must already exist before you can link them)"
            if SETTINGS["_debug"] and SETTINGS["_debug_level"] >= 1:
                logger.debug(result["fail_reason"])
            return result

    result["parent_ids"] = parents

    result["cost"] = result["value"] * SETTINGS["_byoc_commit_fee"]

    # if you got this far it's a valid challenge.
    result["valid"] = True

    return result


@db_session()
def buildChallenge(challenge_object, byoc=False):
    if SETTINGS["_debug"]:
        logger.debug(f"building the challenge from {challenge_object['author']}")
    result = challenge_object

    # result = validateChallenge(challenge_object) # force validation...

    if result.get("valid", False) == False:
        # result = validateChallenge(challenge_object)
        return -1

    author = User.get(name=result["author"])

    # if some one is short points to submit a challenge, GMs can grant points via ctrl_ctf.
    if result["cost"] > getScore(author):
        logger.debug("insufficient funds")
        return -1

    if result["valid"] == False:
        # something went wrong...
        logger.debug(result)
        logger.debug(result["fail_reason"])
        return -1

    chall_obj_tags = set(
        [t.lower().strip() for t in result["tags"]]
    )  # remove duplicates like ['forensics', 'Forensics', 'FoReNsIcS']
    tags = []
    for tag in chall_obj_tags:
        t = Tag.get(name=tag)
        if t == None:  # meaning a tag like this does not exists
            tags.append(Tag(name=tag))
        else:
            tags.append(t)

    # add a tag for byoc
    if byoc:
        byoc_tag = Tag.get(name="byoc")
        if byoc_tag == None:
            byoc_tag = Tag(name="byoc")
        tags.append(byoc_tag)
    tags = list(set(tags))  # incase someone added byoc tag manually

    # if challenge_object.get('bulk'): # this should be the bulk creation method / not BYOC; a way for us to load challenges described in json files. it will populate ALL fields.
    flags = []
    for f in result.get("flags", []):
        fo = Flag(
            flag=f.get("flag_flag"), value=f.get("flag_value"), author=author, tags=tags
        )
        flags.append(fo)

    parents = []
    for parent in result.get("parent_ids", []):
        c = Challenge.get(id=parent)
        parents.append(c)
    # breakpoint()
    chall = Challenge(
        title=result.get("challenge_title"),
        description=result["challenge_description"],
        author=author,
        flags=flags,
        tags=tags,
        parent=parents,
        byoc=result.get("byoc", result.get("byoc", False)),
        byoc_ext_url=result.get("external_validation_url"),
        byoc_ext_value=result.get("value", 0),
    )

    # need to do this so I can get an ID from the chall
    # commit()

    hints = []
    for h in challenge_object.get("hints"):
        ho = Hint(text=h.get("hint_text"), cost=h.get("hint_cost"), challenge=chall)
        hints.append(ho)

    commit()

    bot = User.get(name=SETTINGS["_botusername"])
    fee = Transaction(
        sender=author,
        recipient=bot,
        value=challenge_object["cost"],
        type="byoc commit",
        message=f'submitted challenge "{chall.title}"',
    )

    commit()

    return chall.id
