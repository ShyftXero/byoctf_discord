from collections import Counter
from settings import SETTINGS

from loguru import logger
logger.add('byoctf.log')

from datetime import datetime
from pony.orm import *

db = Database()



class Flag(db.Entity):
    id = PrimaryKey(int, auto=True)
    challenges = Set('Challenge')
    description = Optional(str)
    solves = Set('Solve')
    flag = Required(str)
    value = Required(float)
    unsolved = Optional(bool, default=True)
    bonus = Optional(bool, default=False)
    tags = Set('Tag')
    author = Required('User')
    byoc = Optional(bool)


class Challenge(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    flags = Set(Flag)
    author = Required('User')
    description = Optional(str)
    parent = Set('Challenge', reverse='children')
    children = Set('Challenge', reverse='parent')
    tags = Set('Tag')
    release_time = Optional(datetime, default=lambda: datetime.now())
    visible = Optional(bool, sql_default='True')
    hints = Set('Hint')


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    challenges = Set(Challenge)
    solves = Set('Solve')
    team = Optional('Team')
    sent_transactions = Set('Transaction', reverse='sender')
    recipient_transactions = Set('Transaction', reverse='recipient')
    authored_flags = Set(Flag)


class Solve(db.Entity):
    id = PrimaryKey(int, auto=True)
    time = Optional(datetime, default=lambda: datetime.now())
    flag = Required(Flag)
    user = Required(User)
    value = Required(float)
    transaction = Optional('Transaction')


class Team(db.Entity):
    id = PrimaryKey(int, auto=True)
    members = Set(User)
    name = Required(str)


class Tag(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    challenges = Set(Challenge)
    flags = Set(Flag)


class Transaction(db.Entity):
    id = PrimaryKey(int, auto=True)
    value = Optional(float)
    sender = Required(User, reverse='sent_transactions')
    recipient = Required(User, reverse='recipient_transactions')
    type = Required(str)
    message = Optional(str)
    time = Optional(datetime, default=lambda: datetime.now())
    solve = Optional(Solve)
    hint = Optional('Hint')


class Hint(db.Entity):
    id = PrimaryKey(int, auto=True)
    text = Required(str)
    cost = Optional(float)
    challenge = Required(Challenge)
    transaction = Optional(Transaction)



db.bind(provider='sqlite', filename='byoctf.db', create_db=True)
db.generate_mapping(create_tables=True)

@db_session
def showTeams():
    pass

@db_session
def getTeammates(user) :
    """this includes the user in the list of teammates... """
    res = list(select(member for member in User if member.team.name == user.team.name))
    return res

@db_session
def getScore(user):
    if type(user) == str: # for use via cmdline in ctrl_ctf.py 
        # logger.debug(f'looking for user {user}')
        user = User.get(name=user)
        if user == None:
            return "User is None... "
    # https://docs.ponyorm.org/queries.html#automatic-distinct
    # hence the without_distint()
    received = sum(select(t.value for t in Transaction if t.recipient.name == user.name).without_distinct())
    sent = sum(select(t.value for t in Transaction if t.sender.name == user.name).without_distinct())
    if SETTINGS['_debug'] == True and SETTINGS['_debug_level'] > 1:
        logger.debug(f'{user.name} has received {received}, - sent {sent} = {received - sent}')
    
    return received - sent


@db_session
def challValue(challenge: Challenge):
    flags = list(select(c.flags for c in Challenge if c.id == challenge.id))
    # if SETTINGS['_debug']:
    if SETTINGS['_debug']:
        logger.debug(f'flags{flags}')
    val = sum([flag.value for flag in flags]) 
    # logger.debug(f'challenge {challenge.title} is worth {val} points')
    return val

@db_session()
def topPlayers(num=10):
    all_users = select(u for u in User if u.name != "BYOCTF_Automaton#7840")

    topN = [(u, getScore(u)) for u in all_users]
    if SETTINGS['_debug'] and SETTINGS['_debug_level'] > 1:
        logger.debug(f'topN: {topN}')

    if len(topN) > num:
        return sorted(topN, key=lambda x:x[1],reverse=True)[:num]
    else:
        return sorted(topN, key=lambda x:x[1],reverse=True)

@db_session()
def getTopTeams(num=3):
    all_users = select(u for u in User if u.name != "BYOCTF_Automaton#7840")

    all_scores = [(u, getScore(u)) for u in all_users]
    # logger.debug(f'all_scores: {all_scores}')

    
    scores = {}
    for user, score in all_scores:
        scores[user.team.name] = scores.get(user.team.name, 0) + score 

    sorted_scores = sorted(scores.items(), key=lambda x:x[1], reverse=True)
    if num <= len(sorted_scores):
        res = sorted_scores[:num]
    else:
        res = sorted_scores
    if SETTINGS['_debug'] and SETTINGS['_debug_level'] > 1:    
        logger.debug(f'sorted scores: {res}')
    return res



@db_session()
def challegeUnlocked(user, chall):
    """returns true if all the dependencies for a given challenge have been met by the specified user"""
    # logger.debug(f'{user.name} wants to access {chall.title}')

    # get all solves for this user and their teammates. 

    teammates = getTeammates(user) # including self
    # logger.debug(f'players {[x.name for x in teammates]}')
    # logger.debug(user.team.name)
    team_solves = []
    for teammate in teammates:
        team_solves += list(select(solve.flag for solve in Solve if teammate.name == solve.user.name))
    # logger.debug(f'team_solves {team_solves}')

    # logger.debug(f'"{chall.title}" has a parent "{chall.parent.name}" challenge dependencies {chall.children}')

    parent_flags = list(chall.parent.flags)

    got_all_flags = all(flag in team_solves for flag in parent_flags)
    if SETTINGS['_debug']:
        logger.debug(f'team_solves: {team_solves}')
        logger.debug(f'parent_flags: {parent_flags}')
        logger.debug(f'got_all_flags { got_all_flags}')
    if got_all_flags == True:
        return True
    return False

    

@db_session()
def get_all_challenges(user: User):
    # show only challenges which are not hidden (dependencies resolved and released)

    raw = list(select(c for c in Challenge if c.visible == True ) )

    challs = [c for c in raw if challegeUnlocked(user, c) ]
    # logger.debug(f'indb: {[(x.title, [y for y in x.flags]) for x in challs]}')
    
    return challs

@db_session()
def get_unsolved_challenges(user: User):
    # show only challenges which are not hidden AND unsolved by a user

    # raw = list(select(c for c in Challenge if c.visible == True ) )

    # challs = [c for c in raw if challegeAvailable(user, c) ]
    # logger.debug(challs)
    
    raw = list(select(c for c in Challenge if c.visible == True ) )

    challs = [c for c in raw if challegeUnlocked(user, c) ]

    ret = []
    for chall in challs:
        if SETTINGS['_debug'] and SETTINGS['_debug_level'] > 1:
            logger.debug('flags', list(chall.flags))
        for flag in list(chall.flags):
            # solve = Solve.get(user=user, flag=flag.flag)
            solves = list(select(s for s in Solve if s.user.id == user.id and s.flag.flag == flag.flag))
            if SETTINGS['_debug'] and SETTINGS['_debug_level'] > 1: 
                logger.debug(solves)
            if len(solves) == 0:
                ret.append(chall) 
    return ret


@db_session()
def getMostCommonFlagSolves(num=3):
    solves = Counter(select(solve.flag for solve in Solve))
   
    if SETTINGS['_debug'] and SETTINGS['_debug_level'] > 2:
        logger.debug(solves)
    
    # for solve
    return solves.most_common(num)


@db_session
def getHintTransactions(user:User):
    res = select(t for t in Transaction if t.sender.name == user.name and t.type == 'hint buy')[:]
    return res


@db_session
def buyHint(user:User=None, challenge_id:int=0):
    # this is to abstract away some of the issues with populating test data
    # see around line 400 in buy_hint in byoctf_discord.py

    # does challenge have hints
    # chall = Challenge.get(id=challenge_id)
    # if chall == None:
    #     return None
    chall_hints = list(Challenge.get(id=challenge_id).hints)
    if SETTINGS['_debug']:
        logger.debug(f'got challenge_id {challenge_id} and user {user.name}')
    # has user purchased these hints
    hint_transactions = []
    hints_to_buy = []
    teammates = getTeammates(user)
    for hint in chall_hints:
        hint_transaction = select(t for t in Transaction if t.sender in teammates and t.hint == hint).first()
        # print(hint_transaction)

        if hint_transaction != None: # a purchase exists (not None); no need to buy it again
            continue # so try the next hint in the list of challenge hints
        else:
            hints_to_buy.append(hint)

    if len(hints_to_buy) < 1:
        return "no hints available"

    print(f'hint transactions: {hint_transactions}')    
    print(f'hints available to purchase {hints_to_buy}')
    sorted_hints = sorted(hints_to_buy,key=lambda x:x.cost)
    print(f'sorted hints {sorted_hints}')
    # does user have enough funds
    funds = getScore(user)
    if funds >= sorted_hints[0].cost:
        botuser = User.get(name="BYOCTF_Automaton#7840")
        hint_buy = Transaction(sender=user, recipient=botuser, hint=hints_to_buy[0], value=hints_to_buy[0].cost, type='hint buy', message=f'bought hint for challengeID {challenge_id}')

        # return f'hint purchased for challenge ID {challenge_id}```{sorted_hints[0].text}```'
        return 'ok', hints_to_buy[0]
    return 'insufficient funds'
    

@db_session
def createSolve(value:float=None, user:User=None, flag:Flag=None, msg:str=''):
    botuser = User.get(name='BYOCTF_Automaton#7840')

    if flag.author in getTeammates(user):
        if SETTINGS['_debug'] == True:
            logger.debug(f"{user.name} is trying to submit a flag by a teammate")
        return

    solve = Solve(value=value, user=user, flag=flag)
    solve_credit = db.Transaction(     
        sender=botuser, 
        recipient=user,
        value=value,
        type='solve',
        message=msg,
        solve=solve
    )
    commit()
    



@db_session
def getTeammateScores(user):
    teammates = list(select(member for member in User if member.team.name == user.team.name))
    res = [(tm.name, getScore(tm)) for tm in teammates]
    # for tm in teammates:
    #     logger.debug(tm.name, getScore(tm))

    return res

@db_session()
def validateChallenge(challenge_object):
    logger.debug("validating the challenge from", challenge_object['author'])
    result = {
        'valid': False,
        'author': None,
        'tags': [],
        'challenge_title': "",
        'challenge_description': "",
        'flags': [],
        'hints': [],
        'value': 0, # sum of flags
        'cost': 0
    }
    if SETTINGS['_debug'] and SETTINGS['_debug_level'] >= 1:
        logger.debug("Got challenge_object:", challenge_object)
    # does the challenge_object have all of the fields we need? 
    # title, description, tags, flags with at least one flag, hints 


    if type(challenge_object.get('challenge_title')) == None or len(challenge_object.get('challenge_title')) < 1:
        result['fail_reason'] = 'failed title'
        return result
    result['challenge_title'] = challenge_object['challenge_title']

    if type(challenge_object.get('challenge_description')) == None or (len(challenge_object.get('challenge_description')) < 1 or len(challenge_object.get('challenge_description')) > 1500 ):

        result['fail_reason'] = 'failed description; check length '
        return result
    result['challenge_description'] = challenge_object['challenge_description']
    
    #check that at least one tag exists
    if len(challenge_object['tags']) < 1:
        result['fail_reason'] = 'failed tags exist'
        return result
    for tag in challenge_object['tags']:
        if len(tag) < 1:
            result['fail_reason'] = 'failed tag len'
            return result

    # check the flags
    for flag in challenge_object['flags']:
        # Are the flags unique? not likely to occur, but needs to be checked. this has the potential to leak info about flags that exist. Just make sure they are decent flags. Might just have to accept this risk
        try:
            res = Flag.get(flag=flag.get('flag_flag'))
        except BaseException as e:
            return result
        if res:
            result['fail_reason'] = 'failed flag uniqueness'
            return result
        
        # collect all of the flags from the obj and sum the value then display the cost to post challenge to the user.     
        if flag.get('flag_value') < 0:
            result['fail_reason'] = 'failed flag individual value '
            return result
        result['value'] += flag.get('flag_value')

    # flags aren't worth enough... 100 point minimum
    if result['value'] <= 100 :
        result['fail_reason'] = 'failed flag cumulative value'
        return result

    result['flags'] = challenge_object['flags']
    result['cost'] = result['value'] // 2

    # check the hints. 
    for hint in challenge_object.get('hints',[]):
        if hint.get('hint_cost') < 0: 
            result['fail_reason'] = 'failed hint cost'
            return result
        if len(hint.get('hint_text')) < 1:
            result['fail_reason'] = 'failed hint len'
            return result
    
    # result['hints'] = challenge_object['hints']
    o = []
    for hint in challenge_object.get('hints',[]):
        t = {}
        t['text'] = hint['hint_text']
        t['cost'] = hint['hint_cost']
        o.append(t)
    
    result['hints'] = o


    # if you got this far it's a valid challenge. 
    result['valid'] = True

    return result

@db_session()
def buildChallenge(challenge_object):
    logger.debug("really building the challenge")
    result = validateChallenge(challenge_object)
    if result['valid'] == False:
        # something went wrong... 
        logger.debug(result)
        return
    
    author = User.get(name=challenge_object['author'])

    flags = []
    for f in challenge_object.get('flags'):
        fo = Flag(flag=f.get('flag_flag'), value=f.get('flag_value'), author=author)
        flags.append(fo)

    chall = Challenge(title=challenge_object.get('challenge_title'), flags=flags)
    
    #need to do this so I can get an ID from the chall
    # commit()

    hints = []
    for h in challenge_object.get('hints'):
        ho = Hint(text=h.get('text'), cost=h.get('cost'), challenge=chall)
        hints.append(ho)

    commit()

    bot = User.get(name='BYOCTF_Automaton#7840')
    fee = Transaction(sender=author, recipient=bot, value=challenge_object['cost'], type='byoc commit', message=f'submitted challenge "{chall.title}"')

    commit()


