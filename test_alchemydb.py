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

import alchemydb as adb
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import selectinload
import pytest
import os
import logparse as lp
import asyncio

DB_URL = 'postgresql+asyncpg://postgres:HereInMyGarage@localhost:5432/wessextest'

@pytest.fixture()
def db():
	return adb.DB(db_url=DB_URL)

@pytest.fixture(autouse=True)
async def setup():
	db = adb.DB(db_url=DB_URL)
	await db.reset()


@pytest.fixture()
def alice_user():
	alice_user =  adb.User(playfab_id='386B10B5F82A5456',
					discord_id='146559291745107968',
					nickname='Alice',
					is_admin=True)
	return alice_user


@pytest.mark.asyncio
async def test_alice(db, alice_user):
	async with db.Session() as session:
		#async with session.begin():
		session.add(alice_user)
		res = await session.execute(
			sa.select(adb.User)
			.options(selectinload(adb.User.infractions))
			.options(selectinload(adb.User.actions))
			.filter_by(nickname='Alice'))
		our_user = res.scalars().first()
		assert our_user is not None
		assert our_user is alice_user
		assert our_user.actions == []
		assert our_user.infractions == []
		await session.rollback()


@pytest.mark.asyncio
async def test_persistence(db, alice_user):
	async with db.Session() as session:
		session.add(alice_user)
		await session.commit()
	async with db.Session() as session:
		res = await session.execute(
			sa.select(adb.User)
			.options(selectinload(adb.User.infractions))
			.options(selectinload(adb.User.actions))
			.filter_by(nickname='Alice'))
		our_user = res.scalars().first()
		assert our_user is not None
		await session.delete(our_user)
		await session.commit()
	async with db.Session() as session:
		res = await session.execute(
			sa.select(adb.User)
			.options(selectinload(adb.User.infractions))
			.options(selectinload(adb.User.actions))
			.filter_by(nickname='Alice'))
		our_user = res.scalars().first()
		assert our_user is None


@pytest.mark.asyncio
async def test_adminactions(db, alice_user):
	async with db.Session() as session:
		session.add(alice_user)
		reza_user = adb.User(playfab_id='442291D7DA91C013',
						discord_id='583448737314242570',
						nickname='Reza',
						is_admin=True)
		session.add(reza_user)
		reza_user.infractions = [adb.AdminAction(admin = alice_user,
									action_type='Ban')]
		assert alice_user.actions[0].target == reza_user
		alice_user.actions.append(adb.AdminAction(target = reza_user,
									action_type='Mute'))
		assert reza_user.infractions[1].action_type == 'Mute'


@pytest.mark.asyncio
async def test_get_discordid_from_playfabid(db, alice_user):
	db = adb.DB(db_url=DB_URL)
	async with db.Session() as session:
		session.add(alice_user)
		await session.commit()
		discord_id = await db.get_discordid_from_playfabid(alice_user.playfab_id)
		assert discord_id == alice_user.discord_id


@pytest.mark.asyncio
async def test_logparse(db):
	with open('test/test_ban.log', 'rb') as fp:
		data = fp.read()
	full_log = data.decode()
	#async def msg_handler(logmsg, msgtype, data):
		#assert msgtype == 'ban'
	async with db.Session() as session:
		async def handle_msg(logmsg, msgtype, data):
			await db.handle_msg(logmsg, msgtype, data, session)

		await lp.parse_lines_n(full_log, handle_msg)
		await lp.parse_lines_n(full_log, handle_msg)
		#print(session.dirty)
		await session.commit()
	#assert False


def test_handle_msg(db):
	pass
	