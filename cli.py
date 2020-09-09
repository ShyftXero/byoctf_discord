import fire
import discord

# https://github.com/Tyrrrz/DiscordChatExporter/wiki/Obtaining-Token-and-Channel-IDs#how-to-get-a-user-token

from secrets import USER_TOKEN

DISCORD_BOT = "BYOCTF_Automaton#7840"


client = discord.Client()
client.start()

client.login(USER_TOKEN, bot=False)
client.user.id

byoctf_bot = discord.C

dmchan = discord.DMChannel()

def sendMessage(msg):
    return f'sent message {msg}'

class Commands(discord.Client):
    def sub(self,  flag):
        # print(f"ctx {ctx} ")
        resp = sendMessage(f"!sub {flag}")
        print(resp)

    def solves(self):
        resp = sendMessage(f"!solves")
        print(resp)

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
    client.run(USER_TOKEN, bot=False)


