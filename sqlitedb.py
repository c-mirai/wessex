import asyncio
import aiosqlite
from config import config
import datetime
import logging
from logparse import format_ban, format_unban, timestamp_to_datetime


class db:
    def __init__(self, path=""):
        self.q_get_player = "SELECT * FROM players WHERE PlayFabID="
        if not path:
            self._db_path = config["db"]["db_path"]
        else:
            self._db_path = path

    async def fetch_one(self, sql):
        """Execute an sql command and return a single result from it."""
        async with aiosqlite.connect(self._db_path) as db:
            # print("Executing :" + sql)
            async with db.execute(sql) as cursor:
                return await cursor.fetchone()

    async def fetch_all(self, sql):
        """Execute an sql command and return a single result from it."""
        async with aiosqlite.connect(self._db_path) as db:
            # print("Executing :" + sql)
            async with db.execute(sql) as cursor:
                return await cursor.fetchall()

    async def execute(self, sql):
        """Execute an sql command with no return value."""
        async with aiosqlite.connect(self._db_path) as db:
            print("Executing :" + sql)
            await db.execute(sql)
            await db.commit()

    async def fetch_player(self, playfabid):
        """Return the player data associated with a playfabid."""
        q = self.q_get_player + f"'{playfabid}'"
        return await self.fetch_one(q)

    async def get_player(self, playfabid):
        """Return player data as a dictionary."""
        tup = await self.fetch_player(playfabid)
        if not tup:
            return None
        return {
            "PlayFabID": tup[0],
            "DiscordID": tup[1],
            "LastUsedName": tup[2],
            "IsAdmin": tup[3],
            "LastSeen": tup[4],
            "TotalPlayTime": tup[5],
        }

    async def _table_exists(self, table_name):
        """Check if a table exists."""
        q = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        return await self.fetch_one(q)

    async def _create_ban_table(self):
        """Instantiate the ban table, if it's not already created.

        Returns False if the table already existed, and True otherwise."""
        if await self._table_exists("bans"):
            return False

        q = """
        CREATE TABLE bans (
            BanID INT PRIMARY KEY,
            PlayerID VARCHAR(30) NOT NULL,
            AdminID VARCHAR(30),
            Duration INT,
            Reason VARCHAR(255),
            Time DATETIME,
            Unbanned BOOLEAN,
            FOREIGN KEY(AdminID) REFERENCES players(PlayFabID)
        )
        """
        logging.debug("Executing: " + q)
        await self.execute(q)
        return True

    async def add_ban(self, player_id, admin_id, duration, reason, time=""):
        """Add a ban to the database."""
        if not time:
            time = datetime.datetime.utcnow().isoformat()
        q = f"INSERT INTO bans (PlayerID, AdminID, Duration, Reason, Time, Unbanned) VALUES ('{player_id}', '{admin_id}', {duration}, '{reason}', '{time}', FALSE)"
        

        logging.debug("Executing: " + q)
        await self.execute(q)

    async def is_banned(self, player_id):
        """Return true if player is banned."""
        q = f"SELECT * FROM bans WHERE PlayerID='{player_id}' AND DATETIME(Time, PRINTF('+%u minutes',duration)) > DATETIME('now') AND Unbanned=FALSE"
        return bool(await self.fetch_one(q))

    async def get_bans(self, player_id):
        """Get all bans a player has ever had, except unbanned bans."""
        q = f"SELECT * FROM bans WHERE PlayerID='{player_id}' AND Unbanned=FALSE"
        async with aiosqlite.connect(self._db_path) as db:
            async with db.execute(q) as cursor:
                return await cursor.fetchall()

    async def get_active_bans(self, player_id):
        """Get currently active bans."""
        q = f"SELECT * FROM bans WHERE PlayerID='{player_id}' AND DATETIME(Time, PRINTF('+%u minutes',duration)) > DATETIME('now') AND Unbanned=FALSE"
        async with aiosqlite.connect(self._db_path) as db:
            async with db.execute(q) as cursor:
                return await cursor.fetchall()

    async def unban(self, player_id, time=None):
        """Sets the unbanned flag on any active bans."""
        if not time:
            time="now"
        q = f"UPDATE bans SET Unbanned=TRUE WHERE PlayerID='{player_id}' AND DATETIME(Time, PRINTF('+%u minutes',duration)) > DATETIME('{time}')"
        await self.execute(q)

    async def handle_msg(self, logmsg, msgtype, match):
        if msgtype == "ban":
            (timestamp, adm_name, adm_playfabid, plyr_playfabid, duration, reason) = format_ban(match)
            time = timestamp_to_datetime(timestamp).isoformat()
            await self.add_ban(plyr_playfabid, adm_playfabid, duration, reason, time)
        elif msgtype == "unban":
            (timestamp, adm_name, adm_playfabid, plyr_playfabid) = format_unban(match)
            time = timestamp_to_datetime(timestamp).isoformat()

    async def get_discordid_from_playfabid(self, playfabid):
        """Take a playfabid and return a discord id."""
        res = await self.get_player(playfabid)
        if res:
            return res["DiscordID"]
        return ""

async def main():
    DB = db()
    print(await DB._create_ban_table())
    print(await DB._table_exists("bans"))
    await DB.add_ban("1", "2", 3000, "no rdm test!!!")


if __name__ == '__main__':
    asyncio.run(main())