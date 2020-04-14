from discord.ext import commands

from models.db_ops import DBOperation


class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Commands(bot))
