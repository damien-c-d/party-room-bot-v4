import uuid
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from models.db_ops import DBOperation
from models.utils import valid_donation_channels, in_channels, format_to_k, format_from_k, roles, mention_role, \
    create_embed, create_author_embed, check_donation_roles, high_rank_channels, check_blacklist, \
    get_staff_lists_formatted, get_staff_lists, get_message_counts, get_message_count, channels


class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # region User Commands
    @commands.command(name="invitedby", aliases=["invited by"])
    async def user_invited(self, ctx, *, inviter):
        try:
            staff_channel = ctx.guild.get_channel(channels["discord_staff_room"])
            if isinstance(inviter, discord.Member):
                inviter = inviter.mention
            await staff_channel.send(f"{ctx.author.mention} has joined the server"
                                     f" and was invited by {inviter}")
        finally:
            await ctx.message.delete()

    # endregion User Commands

    # region Donation Commands

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
    @commands.command(name="dupdate", aliases=["donationupdate", "updatedonation"])
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

    @in_channels(valid_donation_channels)
    @commands.guild_only()
    @commands.command(name="top", aliases=["top donations", "topdonations", "topdonators", "topdonors"])
    async def top_(self, ctx):
        db = await DBOperation.new()
        try:
            donations = await db.get_top_10_donors()
            embed = create_embed(title=f"{ctx.guild.name}'s Top Donors", color=discord.Color.blue())
            for donor in donations:
                member = self.bot.get_user(donor[1])
                if member is not None:
                    embed.add_field(name=f"👑 {donor[0]}. {member.display_name}",
                                    value=f"Amount Donated: {donor[2]}")
                else:
                    embed.add_field(name=f"👑 {donor[0]}. deleted-user",
                                    value=f"Amount Donated: {donor[2]}")
            await ctx.send(embed=embed)
        finally:
            await db.close()
            await ctx.message.delete()

    @in_channels(valid_donation_channels)
    @commands.guild_only()
    @commands.command(name="dall", aliases=["all donations", "alldonations", "alldonators", "alldonors"])
    async def all_donors(self, ctx):
        db = await DBOperation.new()
        try:
            donations = await db.get_all_donations()
            text = "All Donators:\n\n"
            for index, donor in enumerate(donations):
                user = self.bot.get_user(donor.get("user_id"))
                if user is not None:
                    text += f"> 👑 {index + 1}. {user.mention}: {format_from_k(donor.get('amount'))}\n"
                else:
                    text += f"> 👑 {index + 1}. deleted-user: {format_from_k(donor.get('amount'))}\n"
            await ctx.send(text)
        finally:
            await db.close()
            await ctx.message.delete()

    # endregion Donation Commands

    # region Blacklist Commands

    @in_channels(high_rank_channels)
    @commands.guild_only()
    @commands.has_any_role(roles["founder"], roles["administrator"], roles["head_moderator"])
    @commands.command(name="gblacklist", aliases=["blacklistadd", "addtoblacklist"])
    async def g_blacklist_(self, ctx, member: discord.Member):
        db = await DBOperation.new()
        try:
            if await check_blacklist(member.id):
                await ctx.send(f"{member.display_name} is already blacklisted.")
            else:
                if await check_blacklist(member.id, False):
                    await db.set_blacklist_active(member.id)
                    await ctx.send(f"{member.display_name}s blacklisting is now active.")
                else:
                    await db.add_to_blacklist(member.id)
                    await ctx.send(f"{member.display_name} has been blacklisted for giveaways")
        finally:
            await db.close()
            await ctx.message.delete()

    @in_channels(high_rank_channels)
    @commands.guild_only()
    @commands.has_any_role(roles["founder"], roles["administrator"], roles["head_moderator"])
    @commands.command(name="unblacklist", aliases=["blacklistremove", "removefromblacklist"])
    async def unblacklist_(self, ctx, member: discord.Member):
        db = await DBOperation.new()
        try:
            await db.delete_from_blacklist(member.id)
            await ctx.send(f"{member.display_name} was deleted from the blacklist.")
        finally:
            await db.close()
            await ctx.message.delete()

    @in_channels(high_rank_channels)
    @commands.guild_only()
    @commands.has_any_role(roles["founder"], roles["administrator"], roles["head_moderator"])
    @commands.command(name="blacklist", aliases=["showblacklist", "blacklisted"])
    async def blacklist_(self, ctx):
        db = await DBOperation.new()
        try:
            blacklist_string = ""
            blacklist = await db.get_blacklist()
            for index, record in enumerate(blacklist):
                user = self.bot.get_user(record.get("user_id"))
                if user is not None:
                    blacklist_string += f"{index + 1}. {user.display_name} - Active: {str(record.get('status'))}\n"
                else:
                    blacklist_string += f"{index + 1}. deleted-user - Active: {str(record.get('status'))}\n"
            await ctx.send(blacklist_string)
        finally:
            await db.close()
            await ctx.message.delete()

    # endregion Blacklist Commands

    # region Moderation Commands

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"], roles["moderator"])
    @commands.command(name="woflist", aliases=["wof", "walloffame"])
    async def wof_list_(self, ctx):
        try:
            role = ctx.guild.get_role(roles["wall_of_fame"])
            if role is not None:
                list_str = [f"{x.display_name} - Joined {(datetime.utcnow() - x.joined_at).days}" for x in role.members]
                list_str.sort()
                await ctx.send(embed=create_embed("Wall Of Fame List", " ".join(list_str), discord.Color.green()))
        finally:
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"], roles["moderator"])
    @commands.command(name="checkrole", aliases=["rolecheck", "userswithrole"])
    async def role_check_(self, ctx, role: discord.Role):
        try:
            users_with_role = [f"**{x.display_name}**\n" for x in role.members]
            await ctx.send(embed=create_embed(f"{role.name} List", " ".join(users_with_role), discord.Color.blurple()))
        finally:
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"], roles["moderator"])
    @commands.command(name="stafflist", aliases=["allstaff"])
    async def staff_list_(self, ctx):
        try:
            staff_list = get_staff_lists_formatted(ctx.guild)
            embed = create_embed("Staff & Helper List",
                                 "A list of staff and helpers with their status at time of this message.",
                                 discord.Color.red())
            for x in staff_list:
                if x[1]:
                    embed.add_field(name=x[0], value=" ".join(x[1]))
            await ctx.send(embed=embed)
        finally:
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"])
    @commands.command(name="staffperformance", aliases=["staffperf", "perflist"])
    async def staff_performance_(self, ctx):
        try:
            staff_list = get_staff_lists(ctx.guild)
            embed = create_embed("Staff & Helper List",
                                 "A list of staff and helpers with their status and msg count at time of this message.",
                                 discord.Color.red())
            for x in staff_list:
                if x[1]:
                    counts = await get_message_counts(ctx.guild, x[1])
                    embed.add_field(name=x[0], value=" ".join(counts))
            await ctx.send(embed=embed)
        finally:
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"])
    @commands.command(name="msghistory", aliases=["messagehistory", "msgcount", "messagecount"])
    async def message_history(self, ctx, member: discord.Member, days: str):
        try:
            if not days.isdigit():
                return await ctx.send("Days must be a number")
            await ctx.send(f"{member.display_name} has sent "
                           f"{await get_message_count(ctx.guild, member, int(days))} "
                           f"in the past {days} days.")
        finally:
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"], roles["moderator"])
    @commands.command(name="mute", aliases=["shh", "shush", "quiet", "stfu", "silenceikillu"])
    async def mute_(self, ctx, member: discord.Member, time: int = 60, *, reason="None"):
        db = await DBOperation.new()
        try:
            end_date = datetime.now() + timedelta(minutes=time)
            mute = await db.get_mute(member.id)
            if mute is None:
                await db.add_mute(member.id)
            else:
                await db.update_mute(member.id, end_date)
            muted_role = ctx.guild.get_role(roles["muted"])
            if muted_role not in member.roles:
                await member.add_roles(muted_role, reason=reason)
            await ctx.send(f"{member.display_name} has been shushed by {ctx.author.display_name} for {time} minutes")
        finally:
            await db.close()
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"], roles["moderator"])
    @commands.command(name="unmute", aliases=["unshh", "unshush", "unquiet", "unstfu"])
    async def unmute_(self, ctx, member: discord.Member):
        muted_role = ctx.guild.get_role(roles["muted"])
        db = await DBOperation.new()
        try:
            mute = await db.get_mute(member.id)
            if mute is None:
                return await ctx.send(f"{member.display_name} is not currently muted.")
            else:
                await db.remove_mute(member.id)
                if muted_role in member.roles:
                    await member.remove_roles(muted_role)
                await ctx.send(f"{member.display_name} has been unmuted by {ctx.author.display_name}")
        finally:
            await db.close()
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"], roles["moderator"])
    @commands.command(name="purge", aliases=["purge_messages", "purgemessages", "bulkdelete", "delete"])
    async def purge_messages_(self, ctx, num, member: discord.Member = None):
        try:
            if member is None:
                deleted = await ctx.channel.purge(limit=num+1, bulk=True)
                return await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
            else:
                deleted = await ctx.channel.purge(limit=num+1, check=lambda m: m.author.id == member.id, bulk=True)
                return await ctx.send(f"Deleted {len(deleted)} of {member.display_name}'s messages.")
        except discord.Forbidden:
            return await ctx.send("I am missing the MANAGE_MESSAGES permission for this channel.")
        except discord.HTTPException:
            return await ctx.send("Failed to purge all the messages.")
        finally:
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"])
    @commands.command(name="clearreactions", aliases=["clearreacts"])
    async def clear_reactions(self, ctx, message_id):
        try:
            message = await ctx.channel.history(limit=1).filter(lambda m: m.id == message_id).flatten()
            if not message:
                message = await ctx.channel.fetch_message(message_id)
                if message is None:
                    return await ctx.send("Could not find that message in this channel.", delete_after=10)
                else:
                    await message.clear_reactions()
            else:
                await message[0].clear_reactions()
        finally:
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"], roles["moderator"], roles["cc_moderator"])
    @commands.command(name="todo")
    async def to_do_(self, ctx, priority: int = 1, *, item: str = None):
        db = await DBOperation.new()
        try:
            if item is None:
                return await ctx.send("If you want Jim to do something, you should type said thing.")
            if 0 < priority <= 3:
                await db.add_todo_item(item, priority, ctx.author.display_name, ctx.author.id)
                await ctx.send(f"Added {item} to Jim's to-do list.")
            else:
                return await ctx.send("Priority must be between 1 and 3:\n"
                                      "1 = Low, 2 = Medium, 3 = High")
        finally:
            await db.close()
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"])
    @commands.command(name="todolist")
    async def to_do_list(self, ctx):
        priorities = {"3": "High", "2": "Medium", "1": "Low"}
        db = await DBOperation.new()
        try:
            items = await db.select_all_todo()
            embed = create_embed("To-Do List", color=discord.Color.red())
            if items and items is not None:
                for index, record in enumerate(items):
                    embed.add_field(name=f"{index+1}. {record.get('todo_id')} "
                                         f"- Priority: {priorities[record.get('priority_num')]}",
                                    value=f"{record.get('item')}\n"
                                          f"Added by {record.get('author_name')} "
                                          f"{(datetime.now() - record.get('datetime_added')).days} days ago.")
                await ctx.send(embed=embed)
            else:
                await ctx.send("To-Do List is Empty!")
        finally:
            await db.close()
            await ctx.message.delete()

    @commands.guild_only()
    @commands.has_any_role(roles["administrator"], roles["founder"])
    @commands.command(name="tododone")
    async def to_do_done(self, ctx, todo_id: uuid.UUID):
        db = await DBOperation.new()
        try:
            todo = await db.get_todo(todo_id)
            if todo_id is None:
                return await ctx.send("Could not find that item on the list.")
            else:
                await db.remove_todo(todo_id)
                await ctx.send(f"<@{todo.get('author_id')}> the item you added: {todo.get('item')} has been completed"
                               f" and removed from the to-do list.")
        finally:
            await db.close()
            await ctx.message.delete()


    # endregion Moderation Commands


def setup(bot):
    bot.add_cog(Commands(bot))
