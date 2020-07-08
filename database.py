from collections import Counter

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


class Hint(db.Entity):
    id = PrimaryKey(int, auto=True)
    text = Required(str)
    cost = Optional(float)
    challenge = Required(Challenge)


db.bind(provider='sqlite', filename='byoctf.db', create_db=True)
db.generate_mapping(create_tables=True)

@db_session
def showTeams():
    pass

@db_session
def getTeammates(user):
    """this includes the user in the list of teammates... """
    return list(select(member for member in User if member.team.name == user.team.name))


@db_session
def challValue(challenge: Challenge):
    flags = list(select(c.flags for c in Challenge if c.id == challenge.id))
    # logger.debug(f'flags{flags}')
    val = sum([flag.value for flag in flags]) 
    # logger.debug(f'challenge {challenge.title} is worth {val} points')
    return val

@db_session()
def topPlayers(num=10):
    # users =db.select((solve.user, solve.value) for solve in Solve)
    logger.debug('This score is wrong.... needs to be based on transactions.')
    solves = select((s.user, sum(s.value)) for s in Solve) # this is an aggregating function; sum() in select
    #TODO either add solves to s
    # this needs to account for transactions sent or received

    # for solve in solves:
    #     logger.debug(solve)
    # points = sum(select(solve.value for solve in Solve if user.name == solve.user.name))
    if len(solves) > num:
        return sorted(solves, key=lambda x:x[1],reverse=True)[:num]
    else:
        return sorted(solves, key=lambda x:x[1],reverse=True)

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
    # logger.debug(f'team_solves: {team_solves}')
    # logger.debug(f'parent_flags: {parent_flags}')
    # logger.debug(f'got_all_flags { got_all_flags}')
    if got_all_flags == True:
        return True
    return False

    # # if ALL flags from this challenge are in in the solves 
    # chall_flags = [flag.flag for flag in list(chall.parent.flags)]

    # num_cflags = len(chall_flags)
    # count = 0

    # # logger.debug(f'chall_flags {chall_flags}')
    # for cflag in chall_flags:
    #     # logger.debug(f'cflag {cflag.flag}')
    #     if cflag in team_solves:
    #         count += 1 
    
    # logger.debug(f'enough: captured_flags:{count} required_flags:{num_cflags} chall_id:{chall.id} "{chall.title}"')
    # if count == num_cflags:
    #     return True   
    # return False

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
        logger.debug('flags', list(chall.flags))
        for flag in list(chall.flags):
            # solve = Solve.get(user=user, flag=flag.flag)
            solves = list(select(s for s in Solve if s.user.id == user.id and s.flag.flag == flag.flag)) 
            logger.debug(solves)
            if len(solves) == 0:
                ret.append(chall) 
    return ret


@db_session()
def getMostCommonFlagSolves(num=3):
    solves = Counter(select(solve.flag for solve in Solve))
   

    logger.debug(solves)
    
    # for solve
    return solves.most_common(num)

@db_session
def createSolve(value:float=None, user:User=None, flag:Flag=None, msg:str=''):
    botuser = User.get(name='BYOCTF_Automaton#7840')
    solve = Solve(value=value, user=user, flag=flag)
    solve_credit = db.Transaction(     
        sender=botuser, 
        recipient=user,
        value=value,
        type='solve',
        message=msg,
    )
    commit()
    

@db_session
def getScore(user):
    # points = sum(select(solve.value for solve in Solve if user.name == solve.user.name))
    received = sum(select(t.value for t in Transaction if t.recipient.name == user.name))
    sent = sum(select(t.value for t in Transaction if t.sender.name == user.name))
    
    logger.debug(f'received {received}, - sent {sent} = {received - sent}')
    
    return received - sent


    # ts = sum(select(t.value for t in Transaction if t.sender.name == user.name or t.recipient.name != user.name ))

    # return ts

@db_session
def getTeammateScores(user):
    teammates = list(select(member for member in User if member.team.name == user.team.name))
    res = [(tm.name, getScore(tm)) for tm in teammates]
    # for tm in teammates:
    #     logger.debug(tm.name, getScore(tm))

    return res



@db_session()
def getTopTeams(num=3):
    #show all teams scores
    
    # this needs to collect points from the transaction table rather than solve.

    solves =  select(solve for solve in Solve)
    
    scores = {}
    for solve in solves:
        # logger.debug(solve, solve.user,solve.user.team,solve.user.name, type(solve.user))
        scores[solve.user.team.name] = scores.get(solve.user.team.name, 0) + solve.value 
    

    # from pprint import pprint
    sorted_scores = sorted(scores.items(), key=lambda x:x[1], reverse=True)
    if num <= len(sorted_scores):
        res = sorted_scores[:num]
    else:
        res = sorted_scores
    # plogger.debug(res)
    return res


# db.commit()


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

    logger.debug("Got challenge_object:", challenge_object)
    # does the challenge_object have all of the fields we need? 
    # title, description, tags, flags with at least one flag, hints 

    if type(challenge_object.get('challenge_title')) == None or len(challenge_object.get('challenge_title')) < 1:
        result['fail_reason'] = 'failed title'
        return result
    result['challenge_title'] = challenge_object['challenge_title']

    if type(challenge_object.get('challenge_description')) == None or len(challenge_object.get('challenge_description')) < 1:
        result['fail_reason'] = 'failed description'
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
    for hint in challenge_object['hints']:
        if hint.get('hint_cost') < 0: 
            result['fail_reason'] = 'failed hint cost'
            return result
        if len(hint.get('hint_text')) < 1:
            result['fail_reason'] = 'failed hint len'
            return result
    
    result['hints'] = challenge_object['hints']

    # if you got this far it's a valid challenge. 
    result['valid'] = True

    return result

@db_session()
def buildChallenge(challenge_object):
    logger.debug("really  building the challenge")
    result = validateChallenge(challenge_object)
    if result['valid'] == True:
        #pull out all of the parts. 
        logger.debug(result)
        
    
    # it must be valid, so press on.



