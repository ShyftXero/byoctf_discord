import database as db

with db.db_session:

    shyft = db.User.get(name="shyft_xero")

    chall = db.Challenge[5]

    print("shyft and chall available")


    print(f'{chall.title} percent complete = ', db.percentComplete(chall, shyft))
