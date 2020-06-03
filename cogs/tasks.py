from datetime import datetime

import discord
from discord.ext import commands, tasks

from models.db_ops import DBOperation
from models.utils import guild_id, channels


class Tasks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.muted_users = []

    @tasks.loop(minutes=1)
    async def mute_timer(self):
        guild = self.bot.get_guild(guild_id)
        if self.muted_users and self.muted_users is not None:
            for muted_user in self.muted_users:
                if muted_user.get("muted"):
                    member = guild.get_member(muted_user.get("user_id"))
                    if datetime.now() >= muted_user.get("mute_end"):
                        await self.remove_mute(muted_user)
                        try:
                            await member.send("Your mute has ended.")
                        except Exception as e:
                            return
                        channel = guild.get_channel(channels["discord_staff_room"])
                        await channel.send(f"{member.mention}'s mute has ended.")

    @mute_timer.before_loop
    async def load_mutes(self):
        db = await DBOperation.new()
        try:
            self.muted_users.extend(await db.get_mutes())
        finally:
            await db.close()

    async def remove_mute(self, user):
        db = await DBOperation.new()


def setup(bot):
    bot.add_cog(Tasks(bot))
