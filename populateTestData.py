import random

import uuid
from database import *


# import faker

# fake = faker.Faker()

db.drop_all_tables(with_all_data=True)

db.create_tables()

ensure_bot_acct()

AMOUNT_OF_DATA = 10

with db_session:
    # teams; These passwords are sha256 of teamname.
    botteam = db.Team(
        name="botteam",
        password="c588d8717b7c6a898889864d588dbe73b123e751814e8fb7e02ca9a08727fd2f",
    )
    bestteam = db.Team(
        name="bestteam",
        password="af871babe0c44001d476554bd5c4f24a7dfdffc5f5b3da9e81a30cc5bb124785",
    )
    secondteam = db.Team(
        name="secondteam",
        password="4a91b2d386e9c22a1cefdfdc94f97aee2b0ecc727f9365def3aeb1cddb99a75f",
    )
    thirdteam = db.Team(
        name="thirdteam",
        password="7d58bb2ef493e764d1092db4c9baa380a9b7ff4c709aeb658e0c4daa616e7d8b",
    )
    fourthteam = db.Team(
        name="fourthteam",
        password="f565deb27bf8fb653958ee6fb625ede79885c6968f23ab2d9b736daed7de677c",
    )

    pub, priv = generate_keys()
    bestteam.public_key = pub
    bestteam.private_key = priv

    pub, priv = generate_keys()
    secondteam.public_key = pub
    secondteam.private_key = priv

    pub, priv = generate_keys()
    thirdteam.public_key = pub
    thirdteam.private_key = priv

    pub, priv = generate_keys()
    fourthteam.public_key = pub
    fourthteam.private_key = priv

    # users
    # bot = db.User(id=0, name='BYOCTF_Automaton#7840', team=botteam)
    bot = db.User.get(id=0)
    # print(bot)
    # exit()
    shyft = db.User(name="shyft_xero", team=bestteam, is_admin=True)
    fie = db.User(name="fie311", team=bestteam, is_admin=True)
    r3d = db.User(name="combaticus", team=secondteam)
    malloc = db.User(name="blackcatt", team=thirdteam)
    aykay = db.User(name="aykay", team=fourthteam)
    jsm = db.User(name="jsm2191", team=bestteam)
    moonkaptain = db.User(name="moonkaptain", team=secondteam, is_admin=True)
    fractumseraph = db.User(name="fractumseraph", team=fourthteam)

    users = [shyft, fie, r3d, malloc, aykay, jsm, moonkaptain, fractumseraph]
    for u in users:
        rotate_player_keys(u)
    db.commit()
    shyft.api_key = "644fccfc-2c12-4fa1-8e05-2aa40c4ef756"  # to make testing and development easier.
    db.commit()

    # flags
    flag_seed = db.Flag(
        flag="FLAG{seedmoney}", value=1000, author=bot, unsolved=False
    )  # avoid firstblood
    flag_asdf = db.Flag(flag="FLAG{asdf}", value=100, author=malloc, byoc=True)
    flag_ASDF = db.Flag(flag="FLAG{ASDF}", value=200, author=malloc, byoc=True)
    flag_qwer = db.Flag(flag="FLAG{qwer}", value=200, author=fie, byoc=True)
    flag_zxcv = db.Flag(flag="FLAG{zxcv}", value=300, author=r3d, byoc=True)
    flag_nosolve = db.Flag(flag="FLAG{DONT_SOLVE}", value=300, author=r3d)
    flag_dosolve = db.Flag(flag="FLAG{DO_SOLVE}", value=600, byoc=True, author=r3d)
    flag_jkl = db.Flag(flag="FLAG{jkl}", value=200, byoc=True, author=malloc)
    flag_bonus2 = db.Flag(flag="FLAG{bonus2}", value=250, author=bot)
    flag_fgh = db.Flag(flag="FLAG{fgh}", value=150, author=aykay)

    # tags
    byoc_tag = upsertTag(name="byoc")
    pentest_tag = upsertTag(name="pentest")
    forensics_tag = upsertTag(name="forensics")
    reversing_tag = upsertTag(name="reversing")
    puzzle_tag = upsertTag(name="puzzle")
    crypto_tag = upsertTag(name="crypto")
    db.commit()

    # challenges
    bonus_challenge = db.Challenge(
        id=0,
        title="__bonus__",
        description="this is the description for all bonus challenges...",
        author=bot,
    )

    c1 = db.Challenge(
        title="challenge 1",
        description="challenge 1 description",
        flags=[flag_asdf, flag_ASDF],
        author=malloc,
        byoc=True,
        tags=[byoc_tag, puzzle_tag, forensics_tag],
    )
    c2 = db.Challenge(
        title="challenge 2",
        description="challenge 2 description; unlocks c3",
        flags=[flag_qwer],
        author=fie,
        tags=[pentest_tag, forensics_tag, crypto_tag],
    )
    c3 = db.Challenge(
        title="challenge 3",
        description="challenge 3 description; requires c2",
        flags=[flag_qwer],
        author=fie,
        parent=[c2],
        tags=[crypto_tag],
    )

    c4 = db.Challenge(
        title="challenge 4",
        description="challenge 4 description;DONT SOLVE",
        flags=[flag_nosolve],
        author=r3d,
    )

    c5 = db.Challenge(
        title="challenge 5",
        description="challenge 5 description;DO SOLVE",
        flags=[flag_dosolve],
        author=r3d,
        tags=[byoc_tag, pentest_tag, reversing_tag],
    )

    c6 = db.Challenge(
        title="challenge 6",
        description="challenge 6 description;",
        flags=[flag_jkl],
        author=malloc,
        parent=[c5, c4],
        tags=[byoc_tag, pentest_tag, forensics_tag],
    )

    c7 = db.Challenge(
        title="chall 7",
        description="chall 7 desc",
        flags=[flag_fgh],
        author=aykay,
        tags=[forensics_tag],
    )

    c8 = db.Challenge(
        title="chall 8 - variables",
        uuid="b83c07a9-69f9-44b0-855e-ac02514214fd",
        description="""
chall 8 uses _variables_ AND markdown *in* the **description**.
hello, {{PLAYERNAME}}. You are on team '{{TEAMNAME}}'
mainly useful for the webpage
try to use h3 for headings in the challenge 
### Markdown heading
- {\{PLAYERNAME}\} -> {{PLAYERNAME}}
- {\{TEAMNAME}\} -> {{TEAMNAME}}
- {\{TEAMUUID}\} -> {{TEAMUUID}}

#### Another sub heading 
content here
https://someserver.com/{\{TEAMUUID}\}
 will become https://someserver.com/{{TEAMUUID}}

```python
print("code block here")
```
""".strip(),
        flags=[flag_fgh],
        author=aykay,
        tags=[forensics_tag],
    )

    # hints
    c1_h1 = db.Hint(text="try asdf", cost=10, challenge=c1)
    c1_h2 = db.Hint(text="try ASDF", cost=10, challenge=c1)

    c2_h1 = db.Hint(text="try qw", cost=20, challenge=c2)
    c2_h2 = db.Hint(text="try last hint + er", cost=30, challenge=c2)

    c5_h1 = db.Hint(text="try DO_SOLVE", cost=50, challenge=c5)

    # seed funds
    shyft_seed = db.Transaction(sender=bot, recipient=shyft, value=1000, type="seed")
    fie_seed = db.Transaction(sender=bot, recipient=fie, value=1000, type="seed")
    r3d_seed = db.Transaction(sender=bot, recipient=r3d, value=1000, type="seed")
    malloc_seed = db.Transaction(sender=bot, recipient=malloc, value=1000, type="seed")
    jsm_seed = malloc_seed = db.Transaction(
        sender=bot, recipient=jsm, value=1337, type="seed"
    )

    db.commit()

    # hint buys

    shyft_hb_c1 = buyHint(user=shyft, challenge_id=c1.id)
    # shyft_hb_c5 = buyHint(user=shyft, challenge_id=c5.id)

    r3d_hb_c1 = buyHint(user=r3d, challenge_id=c1.id)

    fie_hb_c5 = buyHint(user=fie, challenge_id=c5.id)

    r3d_hb_c2 = buyHint(user=r3d, challenge_id=c2.id)

    # solves
    createSolve(user=r3d, flag=flag_asdf)  # valid solve

    createSolve(user=malloc, flag=flag_asdf)  # valid

    createSolve(user=fie, flag=flag_asdf)  # invalid; teammate can't solve.

    # createSolve(user=shyft, flag=flag_asdf) #test rejection of author solves

    createSolve(user=r3d, flag=flag_asdf)  # test rejection of duplicate solves

    createSolve(user=r3d, flag=flag_ASDF)
    createSolve(user=shyft, flag=flag_qwer)
    createSolve(user=fie, flag=flag_zxcv)
    # createSolve(user=shyft, flag=flag_jkl) # test byoc self solve
    # createSolve(user=fie, flag=flag_jkl) # test byoc duplicate\

    createSolve(user=aykay, flag=flag_asdf)
    createSolve(user=aykay, flag=flag_ASDF)
    createSolve(user=aykay, flag=flag_qwer)
    createSolve(user=aykay, flag=flag_zxcv)
    createSolve(user=aykay, flag=flag_jkl)

    res, tip1 = send_tip(shyft, fie, tip_amount=12, msg="from populateTestData")
    res, tip2 = send_tip(r3d, fie)  # default tip amount
    res, tip3 = send_tip(
        sender=fie, recipient=jsm, tip_amount=17, msg="from populateTestData"
    )
    res, tip4 = send_tip(
        sender=shyft,
        recipient=jsm,
        tip_amount=5,
    )
    res, tip5 = send_tip(sender=jsm, recipient=aykay, tip_amount=50)
    res, tip6 = send_tip(sender=jsm, recipient=shyft, tip_amount=50)

    # # show()
    db.commit()

    msg = f"""
shyft api_key= {shyft.api_key}
/login/{shyft.api_key}
private key = {shyft.private_key}
public key = {shyft.public_key}
""".strip()
    print(msg)
