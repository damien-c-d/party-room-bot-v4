from datetime import timedelta, datetime

import discord

from models.config import Config
from models.exceptions import InvalidTimeException, InvalidWinnerAmount, InvalidRoleException

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
                        roles["donator_5m"], 628861208837095435]

to_seconds = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "n": -10
}


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


async def get_message_count(giveaway, user):
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
    return msg_count


def check_giveaway_role(guild, role_id):
    x = discord.utils.get(guild.roles, id=role_id)
    if role_id not in valid_giveaway_roles:
        raise InvalidRoleException(x)
    if x is None:
        raise InvalidRoleException()
    else:
        return x

