import ssl
import uuid
from datetime import datetime

import asyncpg

from models.config import Config
from models.exceptions import NoActiveGiveawaysException, WinnerPoolNotFoundException, BlackListEmptyException
from models.utils import format_from_k

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

    async def remove_giveaway(self, giveaway_id):
        await self.con.execute("""
        DELETE FROM new_giveaways where giveaway_id=$1
        """, giveaway_id)

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
        UPDATE new_giveaways SET author_id=$2, channel_id=$3, guild_id=$4, winners=$5, role_id=$6,
         prize=$7, active=$8, msg_limited=$9, create_date=$10, end_date=$11 WHERE giveaway_id=$1
        """, giveaway.message.id, giveaway.author.id, giveaway.channel.id, giveaway.guild.id, giveaway.winner_amt,
                               giveaway.role.id, giveaway.prize, True, giveaway.msg_req, giveaway.start_date,
                               giveaway.end_date)

    async def get_giveaway(self, giveaway_id):
        return await self.con.fetchrow("""SELECT * FROM new_giveaways WHERE giveaway_id=$1""",
                                       giveaway_id)

    async def get_all_active(self):
        x = await self.con.fetch("""
        SELECT * FROM new_giveaways where active=$1 and guild_id=$2""", True, 593320299773165578)
        if x is not None:
            return x
        else:
            raise NoActiveGiveawaysException()

    async def get_winner_pool(self, giveaway_id):
        x = await self.con.fetchrow("""
        SELECT * FROM winner_pool WHERE giveaway=$1""", giveaway_id)
        if x is not None:
            return x
        else:
            raise WinnerPoolNotFoundException(giveaway_id)

    async def update_winner_pool(self, giveaway_id, pool):
        await self.con.execute("""UPDATE winner_pool SET pool=$1 WHERE giveaway=$2""", pool, giveaway_id)

    async def get_blacklist(self):
        x = await self.con.fetch("""
        SELECT * FROM blacklist
        """)
        if x is not None:
            return x
        else:
            raise BlackListEmptyException()

    async def get_active_blacklists(self):
        x = await self.get_blacklist()
        active = [y for y in x if y.get("status")]
        if active and active is not None:
            return active
        else:
            return None

    async def delete_from_blacklist(self, user_id):
        await self.con.execute("""DELETE FROM blacklist WHERE user_id=$1""",
                               user_id)

    async def add_to_blacklist(self, user_id):
        await self.con.execute("""INSERT INTO blacklist (user_id, status, date_listed) VALUES ($1, $2, $3)""",
                               user_id, True, datetime.now())

    async def get_inactive_blacklists(self):
        x = await self.get_blacklist()
        inactive = [z for z in x if not z.get("status")]
        if inactive and inactive is not None:
            return inactive
        else:
            return None

    async def end_giveaway(self, giveaway_id):
        await self.con.execute("""
        UPDATE new_giveaways SET active=$1 WHERE giveaway_id=$2
        """, False, giveaway_id)

    async def add_to_pool(self, giveaway_id, user_id):
        x = await self.con.fetchrow("""SELECT * FROM winner_pool WHERE giveaway=$1""", giveaway_id)
        if x is None:
            await self.con.execute("""INSERT INTO winner_pool (giveaway, pool) VALUES ($1, $2)""",
                                   giveaway_id, [user_id])
        else:
            pool = x.get("pool")
            if user_id not in pool:
                pool.append(user_id)
                await self.con.execute("""UPDATE winner_pool SET pool=$1 WHERE giveaway=$2""",
                                       pool, giveaway_id)
            else:
                return

    async def get_user_donations(self, user_id):
        x = await self.con.fetchrow("""SELECT * FROM donations WHERE user_id=$1""",
                                    user_id)
        if x is not None:
            return x.get("amount")
        else:
            return None

    async def get_community_chest(self):
        x = await self.con.fetchrow("""SELECT * FROM community_chest""")
        if x is not None:
            return [x.get("amount"), x.get("last_updated")]
        else:
            return None

    async def update_community_chest(self, new_amt):
        await self.con.execute("""UPDATE community_chest SET amount=$1, last_updated=$2""",
                               new_amt, datetime.now())

    async def update_donations(self, new_amt, user_id):
        await self.con.execute("""UPDATE donations SET amount=$1 WHERE user_id=$2""",
                               new_amt, user_id)

    async def add_new_donation(self, amount, user_id):
        await self.con.execute("""INSERT INTO donations (user_id, amount, count) VALUES ($1, $2, $3)""",
                               user_id, amount, 1)

    async def get_top_10_donors(self):
        x = await self.con.fetch("""SELECT * FROM donations ORDER BY amount DESC LIMIT 10""")
        if x is not None:
            donations = []
            for index, donor in enumerate(x):
                donations.append((index + 1, donor.get("user_id"), format_from_k(donor.get("amount"))))
            return donations
        else:
            return None

    async def get_all_donations(self):
        x = await self.con.fetch("""SELECT * FROM donations ORDER BY amount DESC""")
        if x is not None:
            return x
        else:
            return None

    async def get_mutes(self):
        x = await self.con.fetch("""SELECT * FROM moderation WHERE muted=$1""", True)
        if x and x is not None:
            return x
        else:
            return None

    async def get_mute(self, user_id):
        x = await self.con.fetchrow("""SELECT * FROM moderation WHERE user_id=$1""", user_id)
        if x is None:
            return None
        else:
            return x

    async def remove_mute(self, user_id):
        await self.con.execute("""UPDATE moderation SET muted=$1 WHERE user_id=$2""", False, user_id)

    async def update_mute(self, user_id, end_date):
        await self.con.execute("""UPDATE moderation SET muted=$1, mute_end=$2 WHERE user_id=$3""", True, end_date, user_id)

    async def add_todo_item(self, item: str, priority: int, name: str, author_id: str):
        await self.con.execute("""INSERT INTO todo (author_id, author_name, item, datetime_added, priority_num, todo_id)
        VALUES ($1, $2, $3, $4, $5, $6)""",
                               author_id, name, item, datetime.now(), priority, uuid.uuid4())

    async def select_all_todo(self):
        x = await self.con.fetch("""SELECT * FROM todo ORDER BY priority_num DESC, datetime_added ASC""")
        if x and x is not None:
            return x
        else:
            return None

    async def remove_todo(self, todo_id):
        await self.con.execute("""DELETE from todo WHERE todo_id=$1""", todo_id)

    async def get_todo(self, todo_id):
        return await self.con.fetchrow("""SELECT * FROM todo WHERE todo_id=$1""", todo_id)

    async def get_version(self):
        x = await self.con.fetchrow("""SELECT * FROM bot_info""")
        if x is not None:
            return x.get("version")

    async def update_version(self, version):
        await self.con.execute("""UPDATE bot_info SET version=$1""", version)

    async def close(self):
        await self.con.close()
