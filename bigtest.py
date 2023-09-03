import random
import uuid
from database import *
import faker
import pony

hashlib

fake = faker.Faker()
with db_session:
    AMOUNT_OF_TEAMS = 25
    AMOUNT_OF_USERS_PER_TEAM = 4  # Only four players per team
    AMOUNT_OF_FLAGS = 40
    AMOUNT_OF_CHALLENGES = 25
    AMOUNT_OF_HINTS_PER_CHALLENGE = 3
    AMOUNT_OF_SOLVES = 1000  # this high number will help ensure that there are duplicate attempts from users to submit the same flag or a flag of a teammate or a flag they

    # Define some tag names
    tag_names = ["byoc", "pentest", "forensics", "reversing", "puzzle", "crypto"]
    tag_names += [fake.word() for i in range(AMOUNT_OF_CHALLENGES)]

    # Get list of all possible tags
    try:
        tags = [upsertTag(name=name) for name in tag_names]
        ensure_bot_acct()
        commit()
    except pony.orm.core.TransactionIntegrityError as e:
        pass

    # Generate teams
    print(f"creating {AMOUNT_OF_TEAMS} teams")
    team_names = set()
    teams = []
    for _ in range(AMOUNT_OF_TEAMS):
        name = fake.company()
        while name in team_names:
            name = fake.company()
        team_names.add(name)
        teams.append(
            db.Team(
                name=name, password=hashlib.sha256(fake.password().encode()).hexdigest()
            )
        )

    # Generate users for each team
    print(f"creating users")
    user_names = set()
    users = []
    for user in db.User.select():  # get exising db objects
        users.append(user)
    for team in teams:
        for _ in range(AMOUNT_OF_USERS_PER_TEAM):
            name = fake.user_name()
            while name in user_names:
                name = fake.user_name()
            user_names.add(name)
            users.append(db.User(name=name, team=team))

    # Generate flags
    print(f"creating {AMOUNT_OF_FLAGS} flags")
    flag_values = set()
    flags = []
    for flag in db.Flag.select():  # get exising db objects
        flags.append(flag)
    for _ in range(AMOUNT_OF_FLAGS):
        flag = "FLAG{" + str(uuid.uuid4()) + "}"
        while flag in flag_values:
            flag = "FLAG{" + str(uuid.uuid4()) + "}"
        flag_values.add(flag)
        flags.append(
            db.Flag(
                flag=flag, value=random.randint(50, 1000), author=random.choice(users)
            )
        )

    # Generate challenges
    print(f"creating {AMOUNT_OF_CHALLENGES} challenges")
    challenges = [
        db.Challenge(
            title="_".join(fake.words(nb=2)).upper(),
            description=fake.text(),
            flags=random.choices(flags, k=random.randint(1, 3)),
            author=random.choice(users),
            parent=db.Challenge.select().random(1),
            children=db.Challenge.select().random(1),
            byoc=random.choice([True, False]),
            tags=random.choices(tags, k=random.randint(1, 3)),
        )
        for _ in range(AMOUNT_OF_CHALLENGES)
    ]

    for chall in db.Challenge.select():  # get exising db objects
        challenges.append(chall)

    # Generate hints for each challenge
    print(
        f"creating {AMOUNT_OF_HINTS_PER_CHALLENGE * AMOUNT_OF_CHALLENGES} hints for challenges"
    )
    hints = [
        db.Hint(text=fake.sentence(), cost=random.randint(10, 50), challenge=challenge)
        for challenge in challenges
        for _ in range(AMOUNT_OF_HINTS_PER_CHALLENGE)
    ]

    # Seed funds
    print("seeding all players 1000 points")
    seed_funds = [
        db.Transaction(
            sender=users[0], recipient=random.choice(users), value=1000, type="seed"
        )
        for _ in range(len(users))
    ]

    # Generate hint buys
    print(f"creating random hint purchases for users")
    hint_buys = [
        buyHint(user=random.choice(users), challenge_id=random.choice(challenges).id)
        for _ in range(AMOUNT_OF_USERS_PER_TEAM * AMOUNT_OF_TEAMS)
    ]

    # Generate solves
    print(f"creating {AMOUNT_OF_SOLVES} solve attempts; valid and invalid")
    solved_flags = set()
    for _ in range(AMOUNT_OF_SOLVES):
        user = random.choice(users)
        if user.name == "BYOCTF_Automaton#7840":
            continue
        chall = random.choice(challenges)
        if chall.id == 0:
            continue
        flags = list(chall.flags)
        print(chall, flags)
        flag = random.choice(flags)
        # while flag.flag in solved_flags:  # Ensure the flag hasn't been solved yet
        # 	flag = random.choice(flags)
        solved_flags.add(flag.flag)
        createSolve(user=user, flag=flag, challenge=chall)

    # Generate random tips
    print(f"creating {AMOUNT_OF_TEAMS * 4} tips")
    solved_flags = set()
    for _ in range(AMOUNT_OF_TEAMS * 4):
        sender = random.choice(users)
        recipient = random.choice(users)
        if "BYOCTF_Automaton#7840" in [sender.name, recipient.name]:
            continue
        if sender.id == 0 or recipient.id == 0:
            continue
        tip_amount = random.randint(-1, 50) + random.random()
        print(f"{sender.name} -> {recipient.name} for {tip_amount}")
        send_tip(sender, recipient, tip_amount=tip_amount)
