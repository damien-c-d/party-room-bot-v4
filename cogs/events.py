import discord
from discord.ext import commands


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener(name="on_member_join")
    async def member_joined(self, member):
        try:
            await member.send("Welcome to the Party Room! If you were invited by someone, please type !invitedby "
                              "followed by the in-game or discord name of who invited you.\n"
                              "e.g. !invitedby party room bot")
        except Exception as e:
            return


def setup(bot):
    bot.add_cog(Events(bot))
