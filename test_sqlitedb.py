# Wessex - A log-reading bot for mordhau.
# Copyright (C) 2021  Morgan Chesser mfreelancedef@gmail.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import sqlitedb
import datetime
import pytest


@pytest.fixture
def db():
    return sqlitedb.db("db/test.db")

@pytest.mark.asyncio
async def test_alice(db):
    # db = sqlitedb.db("db/test.db")
    alice = await db.fetch_player("386B10B5F82A5456")
    assert alice[1] == 146559291745107968


@pytest.mark.asyncio
async def test_none(db):
    # db = sqlitedb.db("db/test.db")
    none = await db.fetch_player("")
    assert none == None


@pytest.mark.asyncio
async def test_create_bantable(db):
    # db = sqlitedb.db("db/test.db")
    await db._create_ban_table()
    assert await db._table_exists("bans")


@pytest.mark.asyncio
async def test_old_admins(db):
    import mydb
    olddb = mydb.db()
    # db = sqlitedb.db("db/test.db")
    for key in olddb._admins:
        plyr = await db.fetch_player(key)
        assert int(olddb._admins[key]["discordid"]) == plyr[1]
        assert plyr[3] == True


@pytest.mark.asyncio
async def test_old_add_ban(db):
    # db = sqlitedb.db("db/test.db")
    count = await db.fetch_one("SELECT COUNT(*) FROM bans")
    await db.add_ban("testid", "testid2", 3000, "reeeason")
    count2 = await db.fetch_one("SELECT COUNT(*) FROM bans")
    assert count2[0] == count[0] + 1
    await db.execute("DELETE FROM bans WHERE PlayerID='testid'")
    count3 = await db.fetch_one("SELECT COUNT(*) FROM bans") 
    assert count3 == count


@pytest.mark.asyncio
async def test_is_banned(db):
    # db = sqlitedb.db("db/test.db")
    assert not await db.is_banned("testid4")
    await db.add_ban("testid4", "testid5", 3000, "reeeason")
    assert await db.is_banned("testid4")
    await db.execute("DELETE FROM bans WHERE PlayerID='testid4'")
    assert not await db.is_banned("testid4")


@pytest.mark.asyncio
async def test_is_banned_time(db):
    # db = sqlitedb.db("db/test.db")
    time = datetime.datetime.utcnow() - datetime.timedelta(0, 59)
    await db.add_ban("testid4", "testid5", 1, "reeeason", time.isoformat())
    assert await db.is_banned("testid4")
    await asyncio.sleep(1)
    assert not await db.is_banned("testid4")
    await db.execute("DELETE FROM bans WHERE PlayerID='testid4'")


@pytest.mark.asyncio
async def test_unban(db):
    # db = sqlitedb.db("db/test.db")
    await db.add_ban("testid6", "testid7", 10000, "")
    assert await db.is_banned("testid6")
    await db.unban("testid7")
    assert await db.is_banned("testid6")
    await db.unban("testid6")
    assert not await db.is_banned("testid6")
    await db.execute("DELETE FROM bans WHERE PlayerID='testid6'")

    time = datetime.datetime.utcnow() - datetime.timedelta(0, 60)
    await db.add_ban("testid6", "testid7", 1, "reeeason", time.isoformat())
    await db.unban("testid6")
    assert await db.fetch_one("SELECT * FROM bans WHERE Unbanned=FALSE AND PlayerID='testid6'")
    await db.execute("DELETE FROM bans WHERE PlayerID='testid6'")


@pytest.mark.asyncio
async def test_unban_time(db):
    # db = sqlitedb.db("db/test.db")
    #2021/1/1 01:01:01
    time_banned = datetime.datetime.utcnow().isoformat()
    dur = 5
    time_unbanned = (datetime.datetime.utcnow() + datetime.timedelta(0, 5*60 + 1)).isoformat()
    await db.add_ban("test", 1, dur, "", time_banned)
    await db.unban("test", time_unbanned)
    assert await db.is_banned("test")
    time_unbanned = (datetime.datetime.utcnow() + datetime.timedelta(0, 5*60 - 1)).isoformat()
    await db.unban("test", time_unbanned)
    assert not await db.is_banned("test")
    await db.execute("DELETE FROM bans WHERE PlayerID='test'")


@pytest.mark.asyncio
async def test_get_bans(db):
    # db = sqlitedb.db("db/test.db")
    await db.add_ban("testid8", "testid9", 10000, "")
    await db.unban("testid8")
    await db.add_ban("testid8", "testid9", 10000, "")
    await db.add_ban("testid8", "testid9", 10000, "")
    res = await db.get_bans("testid8")
    assert len(res) == 2
    await db.execute("DELETE FROM bans WHERE PlayerID='testid8'")
    res = await db.get_bans("testid8")
    assert len(res) == 0


@pytest.mark.asyncio
async def test_get_active_bans(db):
    # db = sqlitedb.db("db/test.db")
    await db.add_ban("testid10", "testid11", 10000, "")
    await db.unban("testid10")
    time = datetime.datetime.utcnow() - datetime.timedelta(0, 60)
    await db.add_ban("testid10", "testid11", 1, "", time.isoformat())
    time = datetime.datetime.utcnow() - datetime.timedelta(0, 59)
    await db.add_ban("testid10", "testid11", 1, "", time)
    await db.add_ban("testid10", "testid11", 1, "", time)
    res = await db.get_active_bans("testid10")
    assert len(res) == 2
    res = await db.get_bans("testid10")
    assert len(res) == 3
    await db.execute("DELETE FROM bans WHERE PlayerID='testid10'")
    res = await db.get_bans("testid10")
    assert len(res) == 0
