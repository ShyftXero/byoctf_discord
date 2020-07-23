#!/usr/bin/env python3
import fire
from settings import SETTINGS

from terminaltables import GithubFlavoredMarkdownTable as mdTable

import database as db


class Commands:

    def showall(self):
        data = [(k,SETTINGS[k]) for k in SETTINGS.iterkeys()]
        data.insert(0, ['Setting', 'Value'])
        table = mdTable(data)
        print(table.table)

    def setkey(self, key=None, val=None):
        if key != None and val != None:
            print(f'setting {key} to "{val}"') 
            SETTINGS[key] = val
        else:
            print("Need both a KEY and a VAL")

    def getkey(self, key=None):
        print(SETTINGS.get(key, default="Key not found"))
        # print(type(SETTINGS.get(key))) # fire is pretty smart and assigns an appropriate data type

    def dashboard(self):
        pass


    def pause_ctf(self):
        print("pausing CTF")
        SETTINGS['ctf_paused'] = True

    def unpause_ctf(self):
        print("unpausing CTF")
        SETTINGS['ctf_paused'] = False

    def hidescores(self):
        print("hiding scores")
        SETTINGS['scoreboard'] = 'private'

    def showscores(self):
        print("showing scores")
        SETTINGS['scoreboard'] = 'public'

    def togglemvp(self):
        SETTINGS['_show_mvp'] = not SETTINGS['_show_mvp']

    def statusmsg(self, msg=None):
        if msg:
            print(f'updating status to "{msg}"')
            SETTINGS['status'] = msg
        print(SETTINGS.get('status', default="Key error; msg not set"))

    def reinit_config(self):
        # import os
        # from settings import CACHE_PATH
        # os.remove(CACHE_PATH+'/cache.*')
        # os.rmdir(CACHE_PATH)
        import settings # force a recreation fo the settings obj and feed it a default config
        settings.init_config() 
        # print("Re initialized diskcache in ", CACHE_PATH)
        print("re-initialized diskcache.")

    def shell(self):
        import os
        # os.system("""ipython -i -c 'from database import *; user1=User.get(id=1); user2=User.get(id=2)'""")
        os.system("ipython -i -c 'import database as db;  user=db.User.get(id=1); user2=db.User.get(id=2); user3=db.User.get(id=3); user4=db.User.get(id=4); use53=db.User.get(id=5)'")

    def set_team(self, username, team ):
        """username is the discord name and discriminator "user#1234" 
            team is the string of the team name "bestteam"
        """
        with db.db_session:
            user = db.User.get(name=username)
            team = db.Team.get(name=team)
            if user and team:
                print(f'{user.name} is currently on team {user.team.name}.')
                res = input(f'Update to {team.name}? [y/N]')
                if res.lower() == 'y':
                    user.team = team
                    db.commit()

    def grant_points(self, user:str, amount:int):
        ''' remember to use '"user#1234"' as the cmdline parameter for user'''
    
        with db.db_session:
            botuser = db.User.get(name=SETTINGS['_botusername'])
            user = db.User.get(name=user)
            if user:
                t = db.Transaction(     
                sender=botuser, 
                recipient=user,
                value=amount,
                type='admin grant',
                message='admin granted points'
                )
                db.commit()
                print(f'granted {amount} points to {user.name}')
            else:
                print('invalid user')


    def get_score(self, user:str):
        ''' remember to use '"user#1234"' as the cmdline parameter for user'''
        # print(f'User {user} has {db.getScore(user)} points')

    @db.db_session
    def sub_as(self, user:str, flag:str):
        # print(f'{user}, {flag}')
        dbuser = db.User.get(name=user)
        dbflag = db.Flag.get(flag=flag)

        #prevent double solve is now handled in createSolve()
        print(f'{dbuser}, {dbflag} <- Neither of these should be None')
        if dbuser and dbflag:
            # print(f"submiting {dbflag.flag} as {dbuser.name}")
            
            db.createSolve(user=dbuser,flag=dbflag)
            return
        
        print(f"Error submitting {flag} as {user}")
    
    @db.db_session
    def subs(self):
        solves = list(db.select((s.time, s.flag.flag, s.user.name, s.value) for s in db.Solve))
        solves.insert(0, ['Time','Flag','User','Value'])
        table  = mdTable(solves)
        print(table.table)



    @db.db_session
    def users(self):
        data = db.select(u for u in db.User)[:]
        
        data = [(u.id, u.name,u.team.name, db.getScore(u)) for u in data]

        data.insert(0, ['ID', 'Name','Team', 'Score'])
        table = mdTable(data)
        print(table.table)


    @db.db_session
    def trans(self):
        ts = list(db.select( (t.id, t.value, t.type, t.sender.name, t.recipient.name,t.message,t.time)for t in db.Transaction))

        ts.insert(0, ["Trans ID", "Value", 'Type','Sender', 'Recipient', 'Message', 'Time'])
        table = mdTable(ts)
        print(table.table)

    @db.db_session
    def drop(self, table:str):
        msg = """this will drop all users or challenges(flags and hints)"""
        print(msg)
        print(f'target {table}')
        confirm = input("are you sure? [y/N]")
        if confirm.lower() != 'y':
            print('aborting... ')
            return
        
        if table == 'user':
            db.User.select().delete(bulk=True)
            print("Deleted Users")
            return
        if table == 'challenges':
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
        if confirm.lower() != 'y':
            print('aborting... ')
            return
        db.Transaction.select().delete(bulk=True)
        db.Solve.select().delete(bulk=True)
        print("Done.")
        self.trans()
        self.subs()
        self.users()

        

    def FULL_RESET(self):
        confirm = input("are you sure? [y/N]")
        if confirm.lower() != 'y':
            print('aborting... ')
            return
        
        import os     
        cmd = """kill -9 `ps -ef |grep byoctf_discord.py |grep -v grep  | awk {'print $2'}`"""
        print(f"killing bot via {cmd}")
        os.system(cmd)
    
        print('Deleting logs')
        os.remove('byoctf.log')

        print("Deleting and recreating database")
        os.remove('byoctf.db')
        from database import db
        self.reinit_config()

        print('Populating test data')
        os.system("python populateTestData.py")

    def toggle_chall(self, chall_id:int):
        try:
            chall_id = int(chall_id)
        except (ValueError, BaseException) as e:
            print("Challenge id must be an int")
            return 
        with db.db_session:
            chall = db.Challenge.get(id=chall_id)
            chall.visible = not chall.visible 
            db.commit()
            print(f'Challenge id {chall.id} "{chall.title}" visible set to {chall.visible}')

    def challs(self):
        with db.db_session:
            challs = list(db.select((chall.id, chall.title,  chall.description[:20], chall.flags, chall.visible, chall.byoc, ) for chall in db.Challenge))
            # data = [c for c in challs]
            challs.insert(0,['ID', 'Title', 'Description', 'Flags', 'Visible', 'BYOC', 'BYOC_External'])
            table = mdTable(challs)
            print(table.table)
            # for chall in challs:
            #     # print(chall)
    
    @db.db_session
    def teams(self):
        teams = db.Team.select()[:]
        data = []
        for t in teams:
            line = [t.name, ', '.join([tm.name for tm in t.members]), t.password]
            # print(line)
            data.append(line)
        data.insert(0,['Team', 'Members', 'Team Password Hash'])
        table = mdTable(data)
        table.inner_row_border = True
        print(table.table)




    @db.db_session
    def bstat(self):

        challs = list(db.select(c for c in db.Challenge))

        # num solves per challenge
        stats = []
        for chall in challs:
            num_solves = list(db.select(s for s in db.Solve if s.challenge == chall))

            chall_rewards = sum(db.select(sum(t.value) for t in db.Transaction if t.type == "byoc reward" and t.challenge == chall).without_distinct())

            line = [chall.id, chall.title, len(num_solves),chall.author.name, chall_rewards]
            
            stats.append(line)
        stats.insert(0, ['Chall ID', 'Title', '# Solves', 'Author', 'Payout'])

        table = mdTable(stats)

        # team total byoc rewards sum
        total_byoc_rewards = sum(db.select(sum(t.value) for t in db.Transaction if t.type == "byoc reward" ))

        print(table.table)
        print(f'\nTotal BYOC rewards granted: {total_byoc_rewards}')

    def flags(self):
        with db.db_session:
            flags = list(db.select((flag.id, flag.flag, flag.value, flag.challenges) for flag in db.Flag))
            for flag in flags:
                print(flag)

    def del_trans(self, trans_id:int):
        try:
            trans_id = int(trans_id)
        except (ValueError, BaseException) as e:
            print("Transaction id must be an int")
            return 
        with db.db_session:
            trans = db.Transaction.get(id=trans_id)

            if trans != None:
                print(f"Transaction from {trans.sender.name} -> {trans.recipient.name} for {trans.type} and amount {trans.value}")
                resp = input(f"Are you sure you want to delete transaction {trans.id}? [y/N]")
                if resp == 'y':
                    t = db.Transaction.get(id=trans_id)
                    t.delete()
                    print("deleted.") 
                    return
                print("cancelled")


    def add_flag(self):
        print("not implemented")
        pass

    def del_flag(self, flag_id):
        print("not implemented")
        pass

    def add_chall(self, json_file, byoc=False):
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
            result['byoc'] = True
        
        else:
            result['byoc'] = False

        if result['valid'] == True:    
            chall_id = db.buildChallenge(result)
            print(f"Challenge ID {chall_id} created attributed to {result['author']} byoc mode was {byoc}.")
        else:
            print(result['fail_reason'])
    
    def del_chall(self, chall_id:int):
        try:
            chall_id = int(chall_id)
        except (ValueError, BaseException) as e:
            print("Challenge id must be an int")
            return 
        with db.db_session:
            chall = db.Challenge.get(id=chall_id)

            if chall != None:
                print(f"{chall.id} - {chall.title}")
                resp = input(f"are you sure you want to delete challenge {chall.id}? [y/N]")
                if resp == 'y':
                    c = db.Challenge.get(id=chall_id)
                    c.delete()
                
                    print("deleted.") 
                    return
                print("cancelled")

if __name__ == '__main__':
    ### fix for displaying help -> https://github.com/google/python-fire/issues/188#issuecomment-631419585
    def Display(lines, out):
        text = "\n".join(lines) + "\n"
        out.write(text)

    from fire import core
    core.Display = Display
    ###
    commands = Commands()
    fire.Fire(commands)

