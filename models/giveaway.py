import discord
from models.config import Config
from datetime import datetime
from datetime import timedelta

from models.db_ops import DBOperation
from models.utils import get_winner_amt, get_end_date, check_giveaway_role

cfg = Config()
data = cfg.data
roles = cfg.roles
channels = cfg.channels
message_req = data["msg_req"]
emoji = "🎉"


class Giveaway(object):

    def __init__(self, message, author, msg_req, time, winners, role, prize):
        self.message = message
        self.author = author
        self.channel = message.channel
        self.guild = message.guild
        self.start_date = datetime.utcnow()
        self.msg_req = msg_req
        self.prize = prize
        self.end_date = get_end_date(time)
        if self.end_date is None or not self.end_date:
            self.timed = False
        else:
            self.timed = True
        self.winner_amt = get_winner_amt(winners)
        self.role = check_giveaway_role(self.guild, role.id)
        self.embed = self.create_embed()
        self.active = True

    def create_embed(self):
        embed = discord.Embed(color=discord.Color.green(),
                              description=f"Started by: {self.author.mention}\n"
                                          f"Role Requirement: "
                                          f"{'None' if self.role.id == roles['none'] else self.role.mention}\n "
                                          f"Message Requirement: "
                                          f"{'Enabled' if self.msg_req else 'Disabled'}")
        embed.title = f"Giveaway! React with {emoji} to enter!"
        embed.set_thumbnail(url="http://thepartyroom.cf/static/favicon.png")
        embed.insert_field_at(index=0, name="Prize:", value=self.prize, inline=True)
        time_remaining = self.get_timer(self.end_date)
        embed.insert_field_at(index=1, name="Winners:", value=str(self.winner_amt), inline=True)
        embed.insert_field_at(index=2, name="Time Remaining:", value=time_remaining, inline=False)
        return embed

    @classmethod
    async def get_existing(cls, guild, ga):
        author = guild.get_member(ga[1])
        channel = guild.get_channel(ga[2])
        message = await channel.history().get(id=ga[0])
        if message is None:
            await cls.remove_giveaway(ga[0])
            return None
        role = guild.get_role(ga[4])
        return cls(message, author, ga[7], ga[9], ga[3], role, ga[5])

    @staticmethod
    def get_timer(end_date):
        """Returns the time remaining from the end date
        :param end_date: (datetime) the date that the giveaway will end
        :returns str: Specifies the time remaining in d,h,m,s"""
        try:
            if end_date is None:
                return "Not Timed."
            total_seconds = (end_date - datetime.now()).total_seconds()
            d = datetime(1, 1, 1) + timedelta(seconds=total_seconds)
            return str("**%d** Days, **%d** Hours, **%d** Minutes, **%d** Seconds"
                       % (d.day - 1, d.hour, d.minute, d.second))
        except Exception as e:
            print(f"Exception in function: get_timer(end_date:{end_date})\n"
                  f"{e}")

    @staticmethod
    def remove_giveaway(param):
        pass

    def __str__(self):
        return f"""<Giveaway\n
        <ID: {self.message.id}>
        <Author Id: {self.author.id} Name: {self.author.display_name}>
        <Channel  Id: {self.channel.id} Name: {self.channel.name}>
        <Guild Id: {self.guild.id} Name: {self.guild.name}>
        <Start Date: {self.start_date}>
        <End Date: {self.end_date}>
        <Msg_Req: {'enabled' if self.msg_req else 'disabled'}>
        <Prize: {self.prize}>
        <Winners: {self.winner_amt}>
        <Role: {self.role}>
        <Active: {'yes' if self.active else 'no'}>
        <Embed: {self.embed}>
        """

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash((self.message, self.author, self.channel, self.guild, self.winner_amt, self.prize,
                     self.role, self.active, self.msg_req, self.start_date, self.end_date))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.message == other.message and self.author == other.author and self.channel == other.channel and \
               self.guild == other.guild and self.winner_amt == other.winner_amt and self.prize == other.prize and \
               self.role == other.role and self.active == other.active and self.msg_req == other.msg_req and \
               self.start_date == other.start_date and self.end_date == other.end_date
