import random

from database import *


import faker

fake = faker.Faker()

db.drop_all_tables(with_all_data=True)

db.create_tables()


AMOUNT_OF_DATA = 10

with db_session:
    
    #teams
    botteam = db.Team(name='botteam') 
    bestteam = db.Team(name="bestteam")
    secondteam = db.Team(name='secondteam')

    #users
    bot = db.User(name='BYOCTF_Automaton#7840', team=botteam)
    shyft = db.User(name='shyft#0760', team=bestteam)
    fie = db.User(name='notfie#4785', team=bestteam)
    r3d = db.User(name='Combaticus#8292', team=secondteam)

    #flags
    flag_asdf = db.Flag(flag="FLAG{asdf}", value=100,  author=shyft)
    flag_ASDF = db.Flag(flag="FLAG{ASDF}", value=200,  author=shyft)
    flag_qwer = db.Flag(flag="FLAG{qwer}", value=200,  author=fie)
    flag_zxcv = db.Flag(flag="FLAG{zxcv}", value=300,  author=r3d)
    flag_nosolve = db.Flag(flag="FLAG{DONT_SOLVE}", value=300,  author=r3d)
    flag_dosolve = db.Flag(flag="FLAG{DO_SOLVE}", value=600,  author=r3d)
    flag_jkl = db.Flag(flag="FLAG{jkl}", value=200,  author=fie)
    
    #flags
    c1 = db.Challenge(title="challenge 1", description="challenge 1 description",flags=[flag_asdf, flag_ASDF], author=shyft,  )
    c2 = db.Challenge(title="challenge 2", description="challenge 2 description; unlocks c3",flags=[flag_qwer], author=fie, )
    c3 = db.Challenge(title="challenge 3", description="challenge 3 description; requires c2",flags=[flag_qwer], author=r3d, parent=[c2] )
    
    c4 = db.Challenge(title="challenge 4", description="challenge 4 description;DONT SOLVE",flags=[flag_nosolve], author=r3d )

    c5 = db.Challenge(title="challenge 5", description="challenge 5 description;DO SOLVE",flags=[flag_dosolve], author=r3d )
    
    c6 = db.Challenge(title="challenge 6", description="challenge 6 description;",flags=[flag_jkl], author=fie, parent=[c5])
    

    #hints

    #solves
    s1 = Solve(value=flag_asdf.value, user=fie, flag=flag_asdf)
    s2 = Solve(value=flag_ASDF.value, user=fie, flag=flag_ASDF)
    s3 = Solve(value=flag_qwer.value, user=shyft, flag=flag_qwer)
    s4 = Solve(value=flag_asdf.value, user=r3d, flag=flag_asdf)
    s5 = Solve(value=flag_zxcv.value, user=fie, flag=flag_zxcv)

    # # show()
    commit()

#     for i in range(AMOUNT_OF_DATA):
#         try:
            
#             t1 = db.Team(name=fake.company())
#             u1 = db.User(name=fake.name(), team=t1)
#             f1 = db.Flag(flag=f"FLAG{{{fake.word()}}}", value=random.randint(50,500), author=u1) # double curly to escape curly braces
#             c1 = Challenge(title=fake.catch_phrase(), description=fake.text(), flags = [f1], author=u1 )
#             print(u1.name, t1.name, f1.flag)
            
#             commit()
#         except BaseException as e:
#             print(e)
            
    
#     for i in range(5):
#         flags = select(f for f in Flag).random(2)
#         children = select(f for f in Challenge).random(2)
#         author = select(u for u in User if u.name == 'shyft#0760').first()
#         print(author)
#         c = Challenge(title=fake.catch_phrase(), flags=flags, children=children, author=author)
#         print(f"Challenge {c.id} title {c.title} value = {sum(select(f.value for f in c.flags))} unlocks children {[c.title for c in c.children]}")
#         commit()
    
#     users = select(u for u in User).random(AMOUNT_OF_DATA//5)
#     flags = select(f for f in Flag).random(AMOUNT_OF_DATA//5)
#     for user, flag in zip(users,flags):
#         flag.unsolved = False
#         s = Solve(value=flag.value, user=user, flag=flag)
#         print('solve: ', s.user.name, s.flag.flag, s.value, s.time)
        
#         commit()
    

# # show all solves
# with db_session:
#     solves = select(solve for solve in Solve)

#     for solve in solves:
#         print(f"{solve.user.name} submitted '{solve.flag.flag}' for {solve.value} points")

