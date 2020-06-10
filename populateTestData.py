import random

from database import *


import faker

fake = faker.Faker()

db.drop_all_tables(with_all_data=True)

db.create_tables()


AMOUNT_OF_DATA = 10

with db_session:
    
    t1 = db.Team(name="bestteam")
    u1 = db.User(name='shyft0760', score=10, team=t1)
    f1 = db.Flag(flag="FLAG{asdf}", value=100)
    # print(u1.name, t1.name, f1.flag)

    # # show()
    commit()

    for i in range(AMOUNT_OF_DATA):
        try:
            
            t1 = db.Team(name=fake.company())
            u1 = db.User(name=fake.name(), score=fake.zipcode(), team=t1)
            f1 = db.Flag(flag=f"FLAG{{{fake.word()}}}", value=random.randint(50,500)) # double curly to escape curly braces
            print(u1.name, t1.name, f1.flag)
            
            commit()
        except BaseException as e:
            print(e)
            
    
    for i in range(5):
        flags = select(f for f in Flag).random(2)
        children = select(f for f in Challenge).random(2)
        author = select(u for u in User if u.name == 'shyft0760').first()
        print(author)
        c = Challenge(title=fake.catch_phrase(), flags=flags, children=children, author=author)
        print(f"Challenge {c.id} title {c.title} value = {sum(select(f.value for f in c.flags))} unlocks children {[c.title for c in c.children]}")
        commit()
    
    users = select(u for u in User).random(AMOUNT_OF_DATA//2)
    flags = select(f for f in Flag).random(AMOUNT_OF_DATA//2)
    for user, flag in zip(users,flags):
        flag.unsolved = False
        s = Solve(value=flag.value, user=user, flag=flag)
        print('solve: ', s.user.name, s.flag.flag, s.value, s.time)
        
        commit()
    

# show all solves
with db_session:
    solves = select(solve for solve in Solve)

    for solve in solves:
        print(f"{solve.user.name} submitted '{solve.flag.flag}' for {solve.value} points")

