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
        os.system("""ipython -i -c 'from database import *; user1=User.get(id=1); user2=User.get(id=2)'""")

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
    def dump_trans(self):
        ts = list(db.select( (t.id, t.value, t.type, t.sender.name, t.recipient.name,t.message,t.time)for t in db.Transaction))

        ts.insert(0, ["Trans ID", "Value", 'Type','Sender', 'Recipient', 'Message', 'Time'])
        table = mdTable(ts)
        print(table.table)

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

    def dump_challs(self):
        with db.db_session:
            challs = list(db.select((chall.id, chall.title,  chall.description[:20], chall.flags, chall.visible) for chall in db.Challenge))
            # data = [c for c in challs]
            challs.insert(0,['ID', 'Title', 'Description', 'Flags', 'Visible'])
            table = mdTable(challs)
            print(table.table)
            # for chall in challs:
            #     # print(chall)
        

    def dump_flags(self):
        with db.db_session:
            flags = list(db.select((flag.id, flag.flag, flag.value, flag.challenges) for flag in db.Flag))
            for flag in flags:
                print(flag)

    def del_trans(self, trans_id):
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
                    db.Transaction[trans_id].delete()
                    print("deleted.") 
                    return
                print("cancelled")


    def add_flag(self):
        print("not implemented")
        pass

    def del_flag(self, flag_id):
        print("not implemented")
        pass

    def add_chall(self, json_file):
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
        if result['valid'] == True:    
            chall_id = db.buildChallenge(result)
            print(f"Challenge ID {chall_id} created attributed to {result['author']}")
        else:
            print(result['fail_reason'])
    
    def del_chall(self, chall_id):
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
                    db.Challenge[chall_id].delete()
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

