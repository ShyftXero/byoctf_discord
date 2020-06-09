from collections import Counter

from datetime import datetime
from pony.orm import *


db = Database()

class Flag(db.Entity):
    id = PrimaryKey(int, auto=True)
    challenges = Set('Challenge')
    description = Optional(str)
    solves = Set('Solve')
    flag = Required(str, unique=True)
    value = Required(float)
    unsolved = Optional(bool, default=True)
    bonus = Optional(bool, default=False)

class Challenge(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Optional(str)
    flags = Set(Flag)
    author = Required('User')
    description = Optional(str)
    parent = Set('Challenge', reverse='children')
    children = Set('Challenge', reverse='parent')



class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    score = Required(float, default=0)
    challenges = Set(Challenge)
    solves = Set('Solve')
    team = Optional('Team')


class Solve(db.Entity):
    id = PrimaryKey(int, auto=True)
    time = Optional(datetime, default=lambda: datetime.now())
    value = Required(float)
    flag = Required(Flag)
    user = Required(User)


class Team(db.Entity):
    id = PrimaryKey(int, auto=True)
    members = Set(User)
    name = Required(str)

db.bind(provider='sqlite', filename='byoctf.db', create_db=True)
db.generate_mapping(create_tables=True)



def populateTestData(amount=3):
    import faker
    import random
    fake = faker.Faker()
    
    db.drop_all_tables(with_all_data=True)

    db.create_tables()


    with db_session:
        
        t1 = db.Team(name="bestteam")
        u1 = db.User(name='shyft0760', score=10, team=t1)
        f1 = db.Flag(flag="FLAG{asdf}", value=100)
        # print(u1.name, t1.name, f1.flag)

        # # show()
        commit()
 
        for i in range(amount):
            try:
                
                t1 = db.Team(name=fake.company())
                u1 = db.User(name=fake.name(), score=fake.zipcode(), team=t1)
                f1 = db.Flag(flag=f"FLAG{{{fake.word()}}}", value=random.randint(50,500)) # double curly to escape curly braces
                print(u1.name, t1.name, f1.flag)
                
                commit()
            except BaseException as e:
                print(e)
                
        
        for i in range(5):
            targets = select(f for f in Flag).random(2)
            children = select(f for f in Flag).random(2)
            author = select(u for u in User if u.name == 'shyft0760').first()
            print(author)
            c = Challenge(title=fake.catch_phrase(), flags=targets, children=children, author=author)
            print(f"Challenge {c.id} title {c.title} value = {sum(select(f.value for f in c.flags))} unlocks children {[c.title for c in c.children]}")
            commit()
        
        users = select(u for u in User).random(amount//2)
        flags = select(f for f in Flag).random(amount//2)
        for user, flag in zip(users,flags):
            flag.unsolved = False
            s = Solve(value=flag.value, user=user, flag=flag)
            print('solve: ', s.user.name, s.flag.flag, s.value, s.time)
            
            commit()
      

    # show all solves
    with db_session:
        solves =  select(solve for solve in Solve)

        for solve in solves:
            print(f"{solve.user.name} submitted '{solve.flag.flag}' for {solve.value} points")


@db_session()
def topPlayers(num=10):
    # users = select((solve.user, solve.value) for solve in Solve)

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



if __name__ == '__main__':
    populateTestData(amount=20)

# db.commit()