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
    malloc = db.User(name='0xDrMalloc#4492', team=secondteam)

    #flags
    flag_seed = db.Flag(flag="FLAG{seedmoney}", value=100, author=bot)
    flag_asdf = db.Flag(flag="FLAG{asdf}", value=100,  author=malloc)
    flag_ASDF = db.Flag(flag="FLAG{ASDF}", value=200,  author=malloc)
    flag_qwer = db.Flag(flag="FLAG{qwer}", value=200,  author=fie)
    flag_zxcv = db.Flag(flag="FLAG{zxcv}", value=300,  author=r3d)
    flag_nosolve = db.Flag(flag="FLAG{DONT_SOLVE}", value=300,  author=r3d)
    flag_dosolve = db.Flag(flag="FLAG{DO_SOLVE}", value=600,  author=r3d)
    flag_jkl = db.Flag(flag="FLAG{jkl}", value=200, byoc=True, author=malloc)


    
    #challenges
    c1 = db.Challenge(title="challenge 1", description="challenge 1 description",flags=[flag_asdf, flag_ASDF], author=shyft,  )
    c2 = db.Challenge(title="challenge 2", description="challenge 2 description; unlocks c3",flags=[flag_qwer], author=fie, )
    c3 = db.Challenge(title="challenge 3", description="challenge 3 description; requires c2",flags=[flag_qwer], author=r3d, parent=[c2] )
    
    c4 = db.Challenge(title="challenge 4", description="challenge 4 description;DONT SOLVE",flags=[flag_nosolve], author=r3d )

    c5 = db.Challenge(title="challenge 5", description="challenge 5 description;DO SOLVE",flags=[flag_dosolve], author=r3d )
    
    c6 = db.Challenge(title="challenge 6", description="challenge 6 description;",flags=[flag_jkl], author=fie, parent=[c5])
    

    #hints
    c1_h1 = db.Hint(text='try asdf', cost=10, challenge=c1)
    c1_h2 = db.Hint(text='try ASDF', cost=10, challenge=c1)
    
    c2_h1 = db.Hint(text='try qw', cost=20, challenge=c2)
    c2_h2 = db.Hint(text='try last hint + er', cost=30, challenge=c2)
    
    c5_h1 = db.Hint(text='try DO_SOLVE', cost=50, challenge=c5)

    # seed funds
    shyft_seed = db.Transaction(sender=bot, recipient=shyft, value=1000, type='seed')
    fie_seed = db.Transaction(sender=bot, recipient=fie, value=1000, type='seed')
    r3d_seed = db.Transaction(sender=bot, recipient=r3d, value=1000, type='seed')

    # seed funds via solve # can't have team members have same solve... 
    createSolve(value=flag_seed.value, user=shyft, flag=flag_seed)
    createSolve(value=flag_seed.value, user=r3d, flag=flag_seed)
    

    commit()
    #hint buys

    # shyft_hb_c1 = buyHint(user=shyft, challenge_id=c1.id)
    # # shyft_hb_c5 = buyHint(user=shyft, challenge_id=c5.id)

    # fie_hb_c5 = buyHint(user=fie, challenge_id=c5.id)

    # r3d_hb_c2 = buyHint(user=r3d, challenge_id=c2.id)


    #solves
    createSolve(value=flag_asdf.value, user=fie, flag=flag_asdf)
    createSolve(value=flag_ASDF.value, user=r3d, flag=flag_ASDF)
    createSolve(value=flag_qwer.value, user=shyft, flag=flag_qwer)
    createSolve(value=flag_asdf.value, user=r3d, flag=flag_asdf)
    createSolve(value=flag_zxcv.value, user=fie, flag=flag_zxcv)

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

