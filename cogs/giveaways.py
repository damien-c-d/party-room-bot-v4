from datetime import datetime

import discord

from models.db_ops import DBOperation
from models.exceptions import InvalidWinnerAmount, InvalidTimeException, InvalidRoleException, EmbedIsNoneException, \
    NoActiveGiveawaysException
from discord.ext import commands, tasks
from models.giveaway import Giveaway

from models.config import Config
from models.utils import valid_giveaway_channels, update_embed_field, choose_giveaway_winners, \
    check_blacklist, check_message_count, add_user_to_pool, get_role

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
            await message.add_reaction(emoji=emoji)
            self.giveaways.append(giveaway)
            db = await DBOperation.new()
            await db.insert_giveaway(giveaway)
            await db.close()
        except InvalidTimeException as ite:
            return await message.edit(content=f"Giveaway creation failed reason: Invalid Time\n"
                                              f"```{ite.message}```", delete_after=60)
        except InvalidWinnerAmount as iwa:
            return await message.edit(content=f"Giveaway creation failed reason: Invalid Winners\n"
                                              f"```{iwa.message}```", delete_after=60)
        except InvalidRoleException as ire:
            return await message.edit(content=f"Giveaway creation failed reason: Invalid Role\n"
                                              f"```{ire.message}```", delete_after=60)
        finally:

            await ctx.message.delete()

    @tasks.loop(seconds=10)
    async def giveaway_handler(self):
        if not self.giveaways:
            pass
        else:
            try:
                await self.bot.wait_until_ready()
                for giveaway in self.giveaways:
                    if giveaway.active and giveaway is not None:
                        if giveaway.message is not None:
                            if giveaway.end_date > datetime.now():
                                time_remaining = Giveaway.get_timer(giveaway.end_date)
                                new_embed = await update_embed_field(giveaway.embed, 2, "Time Remaining",
                                                                     time_remaining)
                                if new_embed is not None:
                                    await giveaway.message.edit(embed=new_embed)
                                else:
                                    raise EmbedIsNoneException(giveaway.message.id)
                            else:
                                await self.end_giveaway(giveaway)

            except Exception as ex:
                print(ex)

    @giveaway_handler.before_loop
    async def load_giveaways(self):
        try:
            db = await DBOperation.new()
            active_giveaways = await db.get_all_active()
            for result in active_giveaways:
                try:
                    giveaway = await Giveaway.get_existing(self.bot.get_guild(result.get("guild_id")), result)
                    if giveaway is not None:
                        self.giveaways.append(giveaway)
                except InvalidRoleException as ire:
                    message = await Giveaway.get_message(self.bot.get_guild(result.get("guild_id")),
                                                         result.get("channel_id"),
                                                         result.get("giveaway_id"))
                    await message.edit(content="Giveaway removed, invalid role detected.", embed=discord.Embed.Empty)
                    await message.clear_reaction(emoji)
                    await Giveaway.remove_giveaway(message.id)
                    continue
            await db.close()
        except NoActiveGiveawaysException as na_ex:
            print("No active giveaways")
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return
        none_role = guild.get_role(roles["testicle"])
        if not self.giveaways or self.giveaways is None:
            return
        if str(payload.emoji) == emoji:
            giveaway = list(filter(lambda g: g.message.id == payload.message_id, self.giveaways))[0]

            if giveaway is not None:
                if not await check_blacklist(payload.user_id):
                    if giveaway.role != none_role and giveaway.role not in member.roles:
                        try:
                            await giveaway.message.remove_reaction(emoji, member)
                            return await member.send("You don't have the required role for this giveaway")
                        except discord.Forbidden:
                            return
                    else:
                        if giveaway.msg_req:
                            if not check_message_count(giveaway, payload.user_id) and \
                                    (await get_role(guild, 611034264581963777)) not in member.roles:
                                try:
                                    await giveaway.message.remove_reaction(emoji, member)
                                    return await member.send(
                                        "Sorry fam, you gotta be more active in the discord to enter!"
                                        "\n`Disclaimer: Spammers will be blacklisted`")
                                except discord.Forbidden:
                                    return
                            else:
                                await add_user_to_pool(giveaway, payload.user_id)
                        else:
                            await add_user_to_pool(giveaway, payload.user_id)

    async def end_giveaway(self, giveaway):
        try:
            winners = await choose_giveaway_winners(giveaway.message.id, giveaway.winner_amt)
            if not winners or winners is None:
                final_embed = await update_embed_field(giveaway.embed, 2,
                                                       "Giveaway has ended. Could not determine a "
                                                       "winner",
                                                       discord.Embed.Empty)
                await giveaway.message.edit(embed=final_embed)
            else:
                winner_str = ""
                for index, winner in enumerate(winners):
                    winner = giveaway.guild.get_member(winner)
                    winner_str += f"> {index + 1}. {winner.mention}\n"
                final_embed = await update_embed_field(giveaway.embed, 2,
                                                       "Giveaway has ended! Winners were:",
                                                       winner_str)
                await giveaway.message.edit(embed=final_embed)
                await giveaway.channel.send(
                    f"{giveaway.author.display_name}'s {giveaway.prize} "
                    f"giveaway has ended! The winners were:\n" + winner_str)
            giveaway.active = False
            await giveaway.remove_giveaway(giveaway.message.id)
        finally:
            self.giveaways.remove(giveaway)


def setup(bot):
    bot.add_cog(Giveaways(bot))
