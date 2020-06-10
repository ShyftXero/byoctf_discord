from collections import Counter

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
    unsolved = Optional(bool)
    bonus = Optional(bool, default=False)
    tags = Set('Tag')


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


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    score = Optional(float, default=0)
    challenges = Set(Challenge)
    solves = Set('Solve')
    team = Optional('Team')


class Solve(db.Entity):
    id = PrimaryKey(int, auto=True)
    time = Optional(datetime, default=lambda: datetime.now())
    flag = Required(Flag)
    user = Required(User)
    value = Required(float)


class Team(db.Entity):
    id = PrimaryKey(int, auto=True)
    members = Set(User)
    name = Required(str)


class Tag(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    challenges = Set(Challenge)
    flags = Set(Flag)

db.bind(provider='sqlite', filename='byoctf.db', create_db=True)
db.generate_mapping(create_tables=True)

def showTeams():
    pass


@db_session()
def topPlayers(num=10):
    # users =db.select((solve.user, solve.value) for solve in Solve)

    solves = select((s.user, sum(s.value)) for s in Solve)

    # for solve in solves:
    #     print(solve)
    # points = sum(select(solve.value for solve in Solve if user.name == solve.user.name))
    if len(solves) > num:
        return sorted(solves, key=lambda x:x[1],reverse=True)[:num]
    else:
        return sorted(solves, key=lambda x:x[1],reverse=True)

@db_session()
def challegeAvailable(user, chall):
    """returns true if all the dependencies for a given challenge have been met by the specified user"""
    print(f'{user.name} wants to access {chall.title}')

    print(f'challenge parent {chall.parent} challenge dependencies {chall.children}')
    return False



@db_session()
def getMostCommonFlagSolves(num=3):
    solves = Counter(select(solve.flag for solve in Solve))
   

    print(solves)
    
    # for solve
    return solves.most_common(num)

@db_session
def getScore(user):
    points = sum(select(solve.value for solve in Solve if user.name == solve.user.name))
    return points


@db_session
def getTeammates(user):
    return list(select(member for member in User if member.team.name == user.team.name))


@db_session
def getTeammateScores(user):
    teammates = list(select(member for member in User if member.team.name == user.team.name))
    res = [(tm.name, getScore(tm)) for tm in teammates]
    # for tm in teammates:
    #     print(tm.name, getScore(tm))

    return res



@db_session()
def getTopTeams(num=3):
    #show all teams scores
    
    solves =  select(solve for solve in Solve)
    
    scores = {}
    for solve in solves:
        # print(solve, solve.user,solve.user.team,solve.user.name, type(solve.user))
        scores[solve.user.team.name] = scores.get(solve.user.team.name, 0) + solve.value 
    

    # from pprint import pprint
    sorted_scores = sorted(scores.items(), key=lambda x:x[1], reverse=True)
    if num <= len(sorted_scores):
        res = sorted_scores[:num]
    else:
        res = sorted_scores
    # pprint(res)
    return res


# db.commit()