#!/usr/bin/env python3
og_print = print
from rich import print
import fire
from pony.orm.core import commit, db_session
from settings import *

if is_initialized() == False:
    init_config()


from terminaltables import AsciiTable as mdTable

import database as db


class Commands:
    def showall(self):
        """Show all of the current settings for byoctf"""
        data = [(k, SETTINGS[k]) for k in SETTINGS.iterkeys()]
        data.insert(0, ["Setting", "Value"])
        table = mdTable(data)
        print(table.table)

    def setkey(self, key=None, val=None):
        """set a key in the diskcache/settings"""
        if key != None and val != None:
            print(f'setting {key} to "{val}"')
            SETTINGS[key] = val
        else:
            print("Need both a KEY and a VAL")

    def getkey(self, key=None):
        """get a key from the diskcache/settings"""
        print(SETTINGS.get(key, default="Key not found"))
        # print(type(SETTINGS.get(key))) # fire is pretty smart and assigns an appropriate data type

    def dashboard(self):
        """not implemented. supposed to be a realtime monitoring interface"""
        pass

    def pause_ctf(self):
        """disable most of the ctf. tips still work I think"""
        print("pausing CTF")
        SETTINGS["ctf_paused"] = True

    def unpause_ctf(self):
        """Make the ctf work again"""
        print("unpausing CTF")
        SETTINGS["ctf_paused"] = False

    def toggle_scores(self):
        """toggle the visibility of the scoreboard; makes showscores and hidescores redundant"""
        if SETTINGS["scoreboard"] == "private":
            SETTINGS["scoreboard"] = "public"
        else:
            SETTINGS["scoreboard"] = "private"

        print(f"Scores are now {SETTINGS['scoreboard']}")

    def hidescores(self):
        """Make scores on scoreboard private"""
        print("hiding scores")
        SETTINGS["scoreboard"] = "private"

    def showscores(self):
        """Make scores on scoreboard public"""
        print("showing scores")
        SETTINGS["scoreboard"] = "public"

    def toggle_mvp(self):
        """Shows the top N players by score regardless of team"""
        SETTINGS["_show_mvp"] = not SETTINGS["_show_mvp"]

    def statusmsg(self, msg=None):
        """update the status message that shows up in !ctfstat"""
        if msg:
            print(f'updating status to "{msg}"')
            SETTINGS["status"] = msg
        print(SETTINGS.get("status", default="Key error; msg not set"))

    def reinit_config(self):
        """This will repopulate the diskcache with the default config provided in settings.py"""
        import settings  # force a recreation fo the settings obj and feed it a default config

        settings.init_config()
        # print("Re initialized diskcache in ", CACHE_PATH)
        print("re-initialized diskcache.")

    def shell(self):
        """drop into an ipython shell with five users loaded (user1-5); mainly for development or answering questions by interrogating the db. You should be able to prototype your db code here."""
        import os

        # os.system("""ipython -i -c 'from database import *; user1=User.get(id=1); user2=User.get(id=2)'""")
        os.system(
            "ipython -i -c 'import database as db;  user=db.User.get(id=1); user2=db.User.get(id=2); user3=db.User.get(id=3); user4=db.User.get(id=4); user5=db.User.get(id=5)'"
        )

    def set_team(self, username, team):
        """username is the discord name and discriminator "user#1234"
        team is the string of the team name "bestteam"
        """
        with db.db_session:
            user = db.User.get(name=username)
            team = db.Team.get(name=team)
            if user and team:
                print(f"{user.name} is currently on team {user.team.name}.")
                res = input(f"Update to {team.name}? [y/N]")
                if res.lower() == "y":
                    user.team = team
                    db.commit()

    @db.db_session
    def grant_points(self, user: str, amount: int):
        """give points to a user from the byoctf_automaton. remember to use '"user#1234"' as the cmdline parameter for user; Can also "grant" negative points to take points away..."""

        botuser = db.User.get(name=SETTINGS["_botusername"])
        user = db.User.get(name=user)
        if user:
            t = db.Transaction(
                sender=botuser,
                recipient=user,
                value=amount,
                type="admin grant",
                message="admin granted points",
            )
            db.commit()
            print(f"granted {amount} points to {user.name}")
        else:
            print("invalid user")

    def get_score(self, user: str):
        """dumps score for a user by name. remember to use '"user#1234"' as the cmdline parameter for user"""
        # print(f'User {user} has {db.getScore(user)} points')

    @db.db_session
    def toggle_byoc_reward(self, chall_id: int):
        chall = db.Challenge[chall_id]
        if chall == None:
            print("no such challenge")
            return
        flag: db.Flag
        for flag in chall.flags:
            flag.reward_capped = not flag.reward_capped
        self.flags()

    @db.db_session
    def sub_as(self, user: str, flag: str):
        """submit a flag on behalf of a user. useful in case a user can't submit (but you know they should be able to) or for testing and development."""
        # print(f'{user}, {flag}')
        dbuser = db.User.get(name=user)
        dbflag = db.Flag.get(flag=flag)

        # prevent double solve is now handled in createSolve()
        print(f"{dbuser}, {dbflag} <- Neither of these should be None")
        if dbuser and dbflag:
            # print(f"submiting {dbflag.flag} as {dbuser.name}")

            db.createSolve(user=dbuser, flag=dbflag)
            return

        print(f"Error submitting {flag} as {user}")

    @db.db_session
    def subs(self):
        """dumps time that a flag was submitted. useful to prove who submitted fastest?"""
        solves = list(
            db.select((s.time, s.flag.flag, s.user.name, s.value) for s in db.Solve)  # type: ignore
        )
        solves.insert(0, ["Time", "Flag", "User", "Value"])
        table = mdTable(solves)
        print(table.table)

    @db.db_session
    def users(self):
        """Dump all users, which team they're on and their individual score."""
        data = db.select(u for u in db.User)[:]

        data = [(u.id, u.name, u.team.name, db.getScore(u)) for u in data]

        data.insert(0, ["ID", "Name", "Team", "Score"])  # type: ignore
        table = mdTable(data)
        print(table.table)

    @db.db_session
    def trans(self):
        """Dumps a list of all transactions from all users. This will allow you to reconstitute a score if needed or analyze if something doesn't work as expected."""
        ts = list(
            db.select(
                (
                    t.id,
                    t.value,
                    t.type,
                    t.sender.name,
                    t.recipient.name,
                    t.message,
                    t.time,
                )
                for t in db.Transaction  # type: ignore
            )
        )

        ts.insert(
            0, ["Trans ID", "Value", "Type", "Sender", "Recipient", "Message", "Time"]
        )
        table = mdTable(ts)
        print(table.table)

    @db.db_session
    def drop(self, table: str):
        """this will drop all users or challenges(flags and hints)"""
        msg = """this will drop all users or challenges(flags and hints)"""
        print(msg)
        print(f"target {table}")
        confirm = input("are you sure? [y/N]")
        if confirm.lower() != "y":
            print("aborting... ")
            return

        if table == "user":
            db.User.select().delete(bulk=True)
            print("Deleted Users")
            return
        if table == "challenges":
            challs = db.Challenge.select()[:]
            for c in challs:
                for t in c.transaction:
                    t.delete()
                for s in c.solve:
                    s.delete()
                for f in c.flags:
                    f.delete()
                for h in c.hints:
                    h.delete()
                    c.delete()

        # db.db.generate_mapping()

    @db.db_session
    def SOFT_RESET(self):
        msg = """this will drop all transactions and solves but leave flags, hints, challenges, and users in place """
        print(msg)
        confirm = input("are you sure? [y/N]")
        if confirm.lower() != "y":
            print("aborting... ")
            return
        db.Transaction.select().delete(bulk=True)
        db.Solve.select().delete(bulk=True)
        print("Done.")
        self.trans()
        self.subs()
        self.users()

    def INIT(self):
        """this will create tables in db with no test data"""
        confirm = input("are you sure? [y/N]")
        if confirm.lower() != "y":
            print("aborting... ")
            return
        self.reinit_config()

        import os

        cmd = """kill -9 `ps -ef |grep byoctf_discord.py |grep -v grep  | awk {'print $2'}`"""
        print(f"killing bot via {cmd}")
        os.system(cmd)

        # print('Deleting logs')
        # try:
        #     os.remove(SETTINGS['_logfile'])
        # except BaseException as e:
        #     print(e)

        # print("Deleting and recreating database")
        # try:
        #     os.remove(SETTINGS['_db_database'])
        # except BaseException as e:
        #     print(e)

        # from database import db, generateMapping
        # self.reinit_config()
        # generateMapping()

    def DEV_RESET(self):
        """This is mainly for development. deletes logs and database and populates some test data."""
        confirm = input("are you sure? [y/N]")
        if confirm.lower() != "y":
            print("aborting... ")
            return

        import os

        cmd = """kill -9 `ps -ef |grep byoctf_discord.py |grep -v grep  | awk {'print $2'}`"""
        print(f"killing bot via {cmd}")
        os.system(cmd)

        print("Deleting logs")
        os.remove(SETTINGS["_logfile"])

        print("Deleting and recreating database")
        os.remove(SETTINGS["_db_database"])
        from database import db

        self.reinit_config()

        print("Populating test data")
        os.system("python populateTestData.py")

    def toggle_chall(self, chall_id: int):
        """Makes a challenge visible or invisible by the !all command"""
        try:
            chall_id = int(chall_id)
        except (ValueError, BaseException) as e:
            print("Challenge id must be an int")
            return
        with db.db_session:
            chall = db.Challenge.get(id=chall_id)
            chall.visible = not chall.visible
            db.commit()
            print(
                f'Challenge id {chall.id} "{chall.title}" visible set to {chall.visible}'
            )

    def challs(self):
        """This dumps the all the challenges"""
        with db_session:

            data = list()
            chal: db.Challenge
            for chal in db.Challenge.select():
                data.append(
                    [
                        chal.id,
                        chal.title,
                        chal.description,
                        "; ".join([f.flag for f in chal.flags]),
                        ",".join([t.name for t in chal.tags]),
                        chal.visible,
                        chal.byoc,
                    ]
                )
            data.insert(
                0,
                [
                    "ID",
                    "Title",
                    "Description",
                    "Flags",
                    "Tags",
                    "Visible",
                    "BYOC",
                    "BYOC_External",
                ],
            )

        table = mdTable(data)
        print(table.table)
        # for chal in data:
        #     print(chall)

    @db.db_session
    def teams(self):
        """This dumps the all the teams"""
        teams = db.Team.select()[:]
        data = []
        for t in teams:
            line = [t.name, ", ".join([tm.name for tm in t.members]), t.password]
            # print(line)
            data.append(line)
        data.insert(0, ["Team", "Members", "Team Password Hash"])
        table = mdTable(data)
        table.inner_row_border = True
        print(table.table)

    @db.db_session
    def change_teamname(self, oldname: str, newname: str):
        """Allows you to update a team if a user made a mistake or is undesirable..."""
        team = db.Team.get(name=oldname)

        resp = input(
            f"Are you sure you want to change team '{oldname}' to '{newname}'? [y/N]"
        )
        if resp == "y":
            team.name = newname
            db.commit()
            print("Done.")
            return
        print("Cancelling... ")

    @db.db_session
    def bstat(self):
        """BYOC stats for all players. useful for the awards ceremony"""
        challs = list(db.select(c for c in db.Challenge))

        # num solves per challenge
        stats = []
        for chall in challs:
            num_solves = list(db.select(s for s in db.Solve if s.challenge == chall))

            chall_rewards = sum(
                db.select(
                    sum(t.value)
                    for t in db.Transaction  # type: ignore
                    if t.type == "byoc reward" and t.challenge == chall
                ).without_distinct()
            )

            line = [
                chall.id,
                chall.title,
                len(num_solves),
                chall.author.name,
                chall_rewards,
            ]

            stats.append(line)
        stats.insert(0, ["Chall ID", "Title", "# Solves", "Author", "Payout"])

        table = mdTable(stats)

        # total byoc rewards sum
        total_byoc_rewards = sum(
            db.select(sum(t.value) for t in db.Transaction if t.type == "byoc reward")
        )

        print(table.table)
        print(f"\nTotal BYOC rewards granted: {total_byoc_rewards}")

    def flags(self):
        """dump all flags... useful for debugging... yeah.... "debugging"..."""
        with db.db_session:
            data = []
            flag: db.Flag
            for flag in db.Flag.select():
                data.append(
                    [
                        flag.id,
                        flag.flag,
                        flag.value,
                        ",".join([c.title for c in flag.challenges]),
                        flag.reward_capped,
                    ]
                )
            data.insert(0, ["ID", "Flag", "Value", "Challenges", "byoc_reward_capped"])
            table = mdTable(data)
            print(table.table)

    def del_trans(self, trans_id: int):
        """delete a transaction by ID. has the effect of undoing something. points stolen, etc."""
        try:
            trans_id = int(trans_id)
        except (ValueError, BaseException) as e:
            print("Transaction id must be an int")
            return
        with db.db_session:
            trans = db.Transaction.get(id=trans_id)

            if trans != None:
                print(
                    f"Transaction from {trans.sender.name} -> {trans.recipient.name} for {trans.type} and amount {trans.value}"
                )
                resp = input(
                    f"Are you sure you want to delete transaction {trans.id}? [y/N]"
                )
                if resp == "y":
                    t = db.Transaction.get(id=trans_id)
                    t.delete()
                    print("deleted.")
                    return
                print("cancelled")

    @db.db_session
    def add_flag(self, submitted_flag: str, value: float):
        """Useful for adhoc or bonus flag creation. not associated with a challenge."""
        print(f"Got flag '{submitted_flag}' for {value} points'")

        # is the flag unique?
        flag = db.Flag.get(flag=submitted_flag)
        if flag:
            print(f"Flag not unique: matches flag id {flag.id}")
            return
        # is the value numeric? allows for positive or negative values here... just incase we need some landmine flags.
        try:
            value = float(value)
        except BaseException as e:
            print("invalid value...", e)
            return
        botuser = db.User.get(name=SETTINGS["_botusername"])
        flag = db.Flag(flag=submitted_flag, value=value, author=botuser, byoc=False)
        db.commit()
        print(f"Flag {flag.id} created: {flag.flag}")

    @db.db_session
    def del_flag(self, flag_id: int):
        """useful for deleting an adhoc or bonus flag."""
        flag = db.Flag.get(id=flag_id)
        if flag == None:
            print("Invalid flag id...")
            return

        resp = input(f"Are you sure you want to delete flag {flag.id}? [y/N]")
        if resp == "y":
            flag.delete()
            db.commit
            print("Done")
            return
        print("Cancelling...")

    def add_chall(self, json_file, byoc=False):
        """load a challenge via the BYOC mechanism. If byoc is True, it will be marked as a byoc challenge and points will be awarded to the author of the challenge and the solver. Add a challenge on behalf of a user."""

        import json

        try:
            raw = open(json_file).read()
            chall_obj = json.loads(raw)
        except FileNotFoundError:
            print("Can't find file:", json_file)
            return
        except json.JSONDecodeError:
            print("Check JSON syntax in file:", json_file)
            return
        result = db.validateChallenge(chall_obj)

        # for byoc loading of challenges. avoids them being tagged as BYOC ; ./ctrl_ctf.py add_chall chall.json byoc=True
        if byoc:
            result["byoc"] = True

        else:
            result["byoc"] = False

        if result["valid"] == True:
            chall_id = db.buildChallenge(result, byoc=byoc)
            print(
                f"Challenge ID {chall_id} created attributed to {result['author']} byoc mode was {byoc}."
            )
        else:
            print(result["fail_reason"])

    def del_chall(self, chall_id: int):
        """delete a challenge by ID. deletes all flags associated."""
        try:
            chall_id = int(chall_id)
        except (ValueError, BaseException) as e:
            print("Challenge id must be an int")
            return
        with db.db_session:
            chall = db.Challenge.get(id=chall_id)

            if chall != None:
                print(f"{chall.id} - {chall.title}")
                resp = input(
                    f"are you sure you want to delete challenge {chall.id}? [y/N]"
                )
                if resp == "y":
                    c = db.Challenge.get(id=chall_id)
                    c.delete()

                    print("deleted.")
                    return
                print("cancelled")


if __name__ == "__main__":
    ### fix for displaying help -> https://github.com/google/python-fire/issues/188#issuecomment-631419585
    def Display(lines, out):
        text = "\n".join(lines) + "\n"
        out.write(text)

    from fire import core

    core.Display = Display
    ###
    commands = Commands()
    fire.Fire(commands)
