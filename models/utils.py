import random
from datetime import timedelta, datetime

import discord
from discord.ext import commands

from models.config import Config
from models.db_ops import DBOperation
from models.exceptions import InvalidTimeException, InvalidWinnerAmount, InvalidRoleException, \
    WinnerPoolNotFoundException

cfg = Config()
channels = cfg.channels
roles = cfg.roles
msg_req = cfg.data["msg_req"]
invalid_message_channels = [channels["goodbye"], channels["announcements"], channels["rules_ranks"],
                            channels["role_list"],
                            channels["account_safety"], channels["logs"], channels["polls_and_apps"],
                            channels["staff_bot_room"], channels["bingo_announcements_rules"], channels["events"],
                            channels["guides_channel"], channels["games"], channels["bot_commands"]]
can_end_with = ('w', 'd', 'h', 'm', 's', 'n')

valid_giveaway_channels = [channels["giveaways"], channels["staff_bot_room"], channels["important_bot_stuff"]]
valid_giveaway_roles = [roles["none"], roles["level_10"], roles["level_20"], roles["level_30"], roles["level_40"],
                        roles["level_50"], roles["wall_of_fame"], roles["nitro_booster"], roles["bot_goat"],
                        roles["donator_5m"], 700159318682632362]

valid_donation_channels = [channels["community_chest"], channels["staff_bot_room"], channels["important_bot_stuff"]]

to_seconds = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "n": -10
}


def in_channel(ch_id):
    """Function for channel check"""

    def predicate(ctx):
        """Predicate function for channel decorator
        :param ctx: The context of the command that invoked this"""
        return ctx.channel.id == ch_id

    return commands.check(predicate)


def in_channels(ch_ids):
    """Function for giveaway channel decorator"""

    def predicate(ctx):
        """Predicate function for channel decorator
        :param ctx: The context of the command that invoked this"""
        return ctx.channel.id in ch_ids

    return commands.check(predicate)


def get_end_date(time):
    """Gets the total seconds for the giveaway, converts and returns datetime.
    :param time: (str) takes in a str containing a number followed by a letter in can_end_with
    :return False: If time doesn't end with value from tuple can_end_with
    :return None: If time ends with 'n' specifying that the giveaway is not timed.
    :return datetime.datetime: Else returns datetime for end_date."""
    if not time.endswith(can_end_with) or len(time) <= 1:
        raise InvalidTimeException(time)
    if time.endswith('n'):
        return None
    else:
        return datetime.now() + timedelta(seconds=int(time[:-1]) * int(to_seconds[str(time[-1:])]))


def get_winner_amt(winners):
    """Gets the integer value of the amount of winners.
    :param winners: (str) Gets the amount of winners in the (num)w format
    :return int: amount of winners less the 'w'
    :return False: if str does not end with 'w'"""
    if not winners.endswith('w') or len(winners) <= 1:
        raise InvalidWinnerAmount(winners)
    return int(winners[:-1])


async def check_message_count(giveaway, user):
    msg_count = 0
    date = datetime.now() - timedelta(days=7)
    for channel in giveaway.guild.channels:
        try:
            if channel.id in invalid_message_channels or channel.type != discord.ChannelType.text:
                continue
            else:
                if msg_count >= msg_req:
                    break
                async for _ in channel.history(limit=None, after=date).filter(lambda m: m.author.id == user):
                    msg_count += 1
                    if msg_count >= msg_req:
                        break
        except discord.Forbidden:
            continue
        finally:
            if msg_count >= msg_req:
                break
    if msg_count >= msg_req:
        return True
    else:
        return False


def get_giveaway_role(guild, role_id):
    x = discord.utils.get(guild.roles, id=role_id)
    if role_id not in valid_giveaway_roles:
        raise InvalidRoleException(x)
    if x is None:
        raise InvalidRoleException()
    else:
        return x


async def add_reactions(message: discord.Message, emojis):
    for emoji in emojis:
        await message.add_reaction(emoji=emoji)


async def check_blacklist(user):
    db = await DBOperation.new()
    try:
        if user not in await db.get_active_blacklists():
            await db.close()
            return False
        else:
            return True
    finally:
        await db.close()


async def update_embed_field(embed, index, name, value):
    if embed is not None:
        embed.set_field_at(index=index, name=name, value=value, inline=False)
        return embed
    else:
        return None


async def add_user_to_pool(giveaway, user_id):
    db = await DBOperation.new()
    try:
        await db.add_to_pool(giveaway.message.id, user_id)
    finally:
        await db.close()


async def choose_giveaway_winners(giveaway_id, winners):
    final_winners = []
    db = await DBOperation.new()
    try:
        pool = (await db.get_winner_pool(giveaway_id)).get("pool")
        if len(pool) < winners:
            winners = len(pool)
        while len(final_winners) < winners:
            random.shuffle(pool)
            choice = random.choice(pool)
            if not await check_blacklist(choice):
                final_winners.append(choice)
                pool.remove(choice)
            else:
                pool.remove(choice)
                continue
        return final_winners
    finally:
        await db.close()


def format_to_k(amount):
    # takes amount as string from message.content
    # returns an integer in K
    if (amount[-1:]).lower() == "m":
        return int(float(str(amount[:-1])) * 1000)
    elif (amount[-1:]).lower() == "k":
        return int(str(amount[:-1]))
    elif (amount[-1:]).lower() == "b":
        return int(float(str(amount[:-1])) * 1000000)
    else:
        return int(float(amount) * 1000)


def format_from_k(amount):
    # takes amount as integer in K
    # returns a string to be printed
    if amount >= 1000000:
        if len(str(amount)) == 7:
            return '{0:.3g}'.format(amount * 0.000001) + "B"
        elif len(str(amount)) == 8:
            return '{0:.4g}'.format(amount * 0.000001) + "B"
        else:
            return '{0:.5g}'.format(amount * 0.000001) + "B"
    elif amount >= 1000:
        if len(str(amount)) == 4:
            return '{0:.3g}'.format(amount * 0.001) + "M"
        elif len(str(amount)) == 5:
            return '{0:.4g}'.format(amount * 0.001) + "M"
        elif len(str(amount)) == 6:
            return '{0:.5g}'.format(amount * 0.001) + "M"
    else:
        return str(amount) + "k"


def mention_role(guild: discord.Guild, role: int):
    role: discord.Role = guild.get_role(role)
    return role.mention


def create_embed(title, description=None, color=discord.Color.red(), inline=False, *args):
    try:
        embed = discord.Embed(title=title, description=description, color=color)
        for arg in args:
            embed.add_field(name=str(arg[0]), value=str(arg[1]), inline=inline)
        embed.timestamp = datetime.utcnow()
        return embed
    except Exception:
        return None


def create_author_embed(author, icon_url, color=discord.Color.red(), inline=False, *args):
    try:
        embed = discord.Embed(color=color)
        embed.set_author(name=author, icon_url=icon_url)
        for arg in args:
            embed.add_field(name=str(arg[0]), value=str(arg[1]), inline=inline)
        embed.timestamp = datetime.utcnow()
        return embed
    except Exception:
        return None


def check_donation_roles(guild, member, amount):
    five_m = guild.get_role(roles["donator_5m"])
    ten_m = guild.get_role(roles["donator_10m"])
    twenty5_m = guild.get_role(roles["donator_25m"])
    fifty_m = guild.get_role(roles["donator_50m"])
    seventy5_m = guild.get_role(roles["donator_75m"])
    hundred_m = guild.get_role(roles["donator_100m"])
    twofifty_m = guild.get_role(roles["donator_250m"])

    if amount >= 5000 and five_m not in member.roles:
        await member.add_roles(five_m)
    if amount >= 10000 and ten_m not in member.roles:
        await member.add_roles(ten_m)
    if amount >= 25000 and twenty5_m not in member.roles:
        await member.add_roles(twenty5_m)
    if amount >= 50000 and fifty_m not in member.roles:
        await member.add_roles(fifty_m)
    if amount >= 75000 and seventy5_m not in member.roles:
        await member.add_roles(seventy5_m)
    if amount >= 100000 and hundred_m not in member.roles:
        await member.add_roles(hundred_m)
    if amount >= 250000 and twofifty_m not in member.roles:
        await member.add_roles(twofifty_m)
