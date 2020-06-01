import discord
from discord.ext import commands

from models.db_ops import DBOperation
from models.utils import valid_donation_channels, in_channels, format_to_k, format_from_k, roles, mention_role, \
    create_embed, create_author_embed, check_donation_roles


class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #   Donation Commands
    #
    #

    reasons = {"1": "Recruitment Drop",
               "2": "Wall Of Fame Drop",
               "3": "Clan Event",
               "4": "Adjustment",
               "5": "Donation",
               "6": "Other"}

    @in_channels(valid_donation_channels)
    @commands.guild_only()
    @commands.command(name="donate")
    async def donate_(self, ctx, amount):
        try:
            if (format_to_k(amount)) < 1000:
                return await ctx.send("There is a minimum donation amount of **1M**")
            else:
                await ctx.send(
                    f"{ctx.author.display_name} has made a donation request of {amount}. Thanks for donating!\n\n"
                    f" an {mention_role(ctx.guild, roles['administrator'])}"
                    f", {mention_role(ctx.guild, roles['bot_goat'])} or {mention_role(ctx.guild, roles['founder'])}"
                    f"will message you to collect!\n\n"
                    f"**Donations are used for - 3x Weekly Recruitment Drop Parties, "
                    f"Monthly Wall of Fame Drops, and our Clanwide Events!**")
        except ValueError:
            return await ctx.send("Invalid amount input. Must be number followed by 'm'\n"
                                  "e.g. !donate 20m\n"
                                  "Minimum donation of 1m.")
        except OverflowError:
            return await ctx.send("That is not a valid donation amount. Repeated abuse of this command will lead "
                                  "to a warning on your account.")
        finally:
            await ctx.message.delete()

    @in_channels(valid_donation_channels)
    @commands.guild_only()
    @commands.command(name="donations", aliases=["mydonations", "checkdonations"])
    async def donations_(self, ctx, member: discord.Member = None):
        db = await DBOperation.new()
        try:
            member: discord.Member = ctx.author if member is None else member
            amount = await db.get_user_donations(user_id=member.id)
            embed = create_author_embed(member.display_name, member.avatar_url, discord.Color.purple()
                                        , False, ["Amount Donated:", format_from_k(amount) if amount is not None else
                "This user has not donated."])
            await db.close()
            return await ctx.send(embed=embed)
        finally:
            await db.close()
            await ctx.message.delete()

    @in_channels(valid_donation_channels)
    @commands.guild_only()
    @commands.has_any_role(roles["founder"], roles["administrator"])
    @commands.command(name="chestupdate", aliases=["updatechest"])
    async def chest_update_(self, ctx, amount, *, reason="6"):
        db = await DBOperation.new()
        try:
            if reason.isdigit():
                if str(reason) in self.reasons:
                    reason = self.reasons[reason]
            chest = await db.get_community_chest()
            if chest is not None:
                total = format_from_k(chest[0] + int(format_to_k(amount)))
                embed = create_embed("Community Chest Update",
                                     f"{ctx.author.metion} {'removed' if format_to_k(amount) < 0 else 'added'} {amount} "
                                     f"from the chest.\n**Reason: {reason}**", discord.Color.purple(), False,
                                     ["Updated Chest Amount:", total])
                embed.set_thumbnail(
                    url="http://img2.wikia.nocookie.net/__cb20111125181201/runescape/images/a/a8"
                        "/Mahogany_prize_chest_POH.png")
                await ctx.send(embed=embed)
                await db.update_community_chest(chest[0] + int(format_to_k(amount)))

        finally:
            await ctx.message.delete()
            await db.close()

    @in_channels(valid_donation_channels)
    @commands.guild_only()
    @commands.command(name="chest", aliases=["communitychest", "checkchest", "chestamt"])
    async def chest_(self, ctx):
        db = await DBOperation.new()
        try:
            chest = await db.get_community_chest()
            embed = create_author_embed(ctx.guild.name, str(ctx.guild.icon_url), discord.Color.green(), False,
                                        ["Current Community Chest Value:", format_from_k(chest[0])],
                                        ["Last Updated:", str(chest[1])])
            embed.set_thumbnail(
                url="http://img2.wikia.nocookie.net/__cb20111125181201/runescape/images/a/a8/Mahogany_prize_chest_POH"
                    ".png")
            await ctx.send(embed=embed)
        finally:
            await db.close()
            await ctx.message.delete()

    @in_channels(valid_donation_channels)
    @commands.guild_only()
    @commands.command(name="dupdate", aliases=["donationupdate","updatedonation"])
    async def donation_update_(self, ctx, member: discord.Member, amount):
        db = await DBOperation.new()
        try:
            if member is None:
                return await ctx.send("Invalid member mentioned.")
            donations = await db.get_user_donations(member.id)
            if donations is not None:
                total = donations[0] + format_to_k(amount)
                await db.update_donations(total, member.id)
                await ctx.send(f"{member.mention}'s donations updated. Thanks for donating <3\n"
                               f"New Total: {format_from_k(total)}\n\n"
                               f"Thats equivalent to {(float(total / 1000) / 5)} Recruitment Drops or"
                               f" {(float(total / 1000) / 40)} WoF Drops.")
            else:
                total = format_to_k(amount)
                await db.add_new_donation(amount, member.id)
                await ctx.send(f"{member.mention} donated for the first time! Thanks for donating <3\n"
                               f"New Total: {format_from_k(total)}\n\n"
                               f"Thats equivalent to {(float(total / 1000) / 5)} Recruitment Drops or"
                               f" {(float(total / 1000) / 40)} WoF Drops.")
            check_donation_roles(ctx.guild, member, total)
        finally:
            await db.close()
            await ctx.message.delete()


def setup(bot):
    bot.add_cog(Commands(bot))
