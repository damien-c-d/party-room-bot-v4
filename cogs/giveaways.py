import discord

from models.db_ops import DBOperation
from models.exceptions import InvalidWinnerAmount, InvalidTimeException, InvalidRoleException
from discord.ext import commands
from models.giveaway import Giveaway

from models.config import Config
from models.utils import valid_giveaway_channels

cfg = Config()
roles = cfg.roles
channels = cfg.channels
emoji = "🎉"


def in_giveaway_channel():
    """Function for giveaway channel decorator"""

    def predicate(ctx):
        """Predicate function for channel decorator
        :param ctx: The context of the command that invoked this"""
        return ctx.channel.id in valid_giveaway_channels

    return commands.check(predicate)


class Giveaways(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.giveaways = []

    @commands.guild_only()
    @commands.has_any_role(roles["moderator"], roles["head_moderator"], roles["administrator"], roles["founder"],
                           roles["bot_goat"])
    @commands.command(name="gactive", aliases=["activegiveaways"])
    async def gactive_(self, ctx):
        active_giveaways = [x for x in self.giveaways if x.active]
        embed = discord.Embed(title="Active Giveaways", color=discord.Color.red())
        for index, giveaway in enumerate(active_giveaways):
            role_req = ctx.guild.get_role(giveaway.role)
            embed.add_field(name=f"#{index + 1}:",
                            value=f"Prize:\n`{giveaway.prize_text}`\n"
                                  f"{f'Requires role: `{role_req.name}`' if role_req.name.lower() != 'none' else '`No Role Required`'}\n"
                                  f"Started By:\n`{giveaway.author.display_name}`\n"
                                  f"Winners To Be Chosen:\n`{giveaway.winners}`\n"
                                  f"In Channel:\n{giveaway.channel.mention}\n"
                                  f"Ends In:\n{await Giveaway.get_timer(giveaway.end_date)}\n", inline=False)
        await ctx.send(embed=embed)
        await ctx.message.delete()

    # @in_giveaway_channel()
    @commands.guild_only()
    # @commands.has_any_role(roles["host"], roles["head_moderator"], roles["administrator"], roles["founder"],
    #                        roles["bot_goat"])
    @commands.command(name="gstart")
    async def _gstart(self, ctx, time, winners, role: discord.Role, *, prize):
        message = await ctx.send("Creating Giveaway...")
        try:
            giveaway = Giveaway(message, ctx.author, self.bot.msq_req_active, time, winners, role, prize)
            await message.edit(content="", embed=giveaway.embed)
            self.giveaways.append(giveaway)
            db = await DBOperation.new()
            await db.insert_giveaway(giveaway)
        except InvalidTimeException as ite:
            return await message.edit(content=ite.message)
        except InvalidWinnerAmount as iwa:
            return await message.edit(content=iwa.message)
        except InvalidRoleException as ire:
            return await message.edit(content=ire.message)
        finally:
            await ctx.message.delete()


def setup(bot):
    bot.add_cog(Giveaways(bot))
