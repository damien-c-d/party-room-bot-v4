import discord
from discord.ext import commands


class Bot(commands.Bot):

    def __init__(self, token, version, main_prefix, music_prefix, msg_req, msg_req_active):
        self.version = version
        super().__init__(command_prefix=commands.when_mentioned_or(main_prefix, music_prefix),
                         case_insensitive=True)
        self.remove_command('help')
        self.token = token
        self.msg_req = msg_req
        self.msq_req_active = msg_req_active

    def run(self):
        super().run(self.token, reconnect=True)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_ready(self):
        await self.change_presence(status=discord.Status.idle,
                                   activity=discord.Activity(type=discord.ActivityType.listening,
                                                             name=f"Commands: !help - Version {self.version}"))
        print(f"Bot logged in as {self.user.name}")
