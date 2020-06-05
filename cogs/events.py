import discord
from discord.ext import commands

from models.db_ops import DBOperation
from models.utils import guild_id, channels


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

    @commands.Cog.listener(name="on_ready")
    async def bot_ready(self):
        db = await DBOperation.new()
        try:
            if await db.get_version() != self.bot.version:
                await db.update_version(self.bot.version)
                guild = self.bot.get_guild(guild_id)
                channel = guild.get_channel(channels["bot_commands"])
                return await channel.send(f"Bot updated to version {self.bot.version}")
        finally:
            await db.close()


def setup(bot):
    bot.add_cog(Events(bot))
