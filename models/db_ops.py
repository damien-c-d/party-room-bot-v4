import ssl

import asyncpg

from models.config import Config

data = Config().data
db_url = data["db_url"]


# noinspection SqlNoDataSourceInspection
class DBOperation:

    def __init__(self, con):
        self.con = con

    @classmethod
    async def new(cls):
        ctx = ssl.create_default_context(cafile='')
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        con = await asyncpg.connect(db_url, ssl=ctx)
        return cls(con)

    async def remove_giveaway(self, giveaway):
        await self.con.execute("""
        DELETE FROM new_giveaways where giveaway_id=$1
        """, giveaway.message.id)

    async def insert_giveaway(self, giveaway):
        await self.con.execute("""
        INSERT INTO new_giveaways (giveaway_id, author_id, channel_id, guild_id, winners, role_id, prize, active, 
        msg_limited, create_date, end_date)
        VAlUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
""", giveaway.message.id, giveaway.author.id, giveaway.channel.id, giveaway.guild.id, giveaway.winner_amt,
                               giveaway.role.id, giveaway.prize, True, giveaway.msg_req, giveaway.start_date,
                               giveaway.end_date)

    async def update_giveaway(self, giveaway):
        await self.con.execute("""
        UPDATE new_giveaways SET giveaway_id=$1, author_id=$2, channel_id=$3, guild_id=$4, winners=$5, role_id=$6,
         prize=$7, active=$8, msg_limited=$9, create_date=$10, end_date=$11
        """, giveaway.message.id, giveaway.author.id, giveaway.channel.id, giveaway.guild.id, giveaway.winner_amt,
                               giveaway.role.id, giveaway.prize, True, giveaway.msg_req, giveaway.start_date,
                               giveaway.end_date)

    async def get_all_active(self):
        return await self.con.fetch("""
        SELECT * FROM new_giveaways where active=$1""", True)

    async def close(self):
        await self.con.close()