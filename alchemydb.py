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

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from util import timestamp_to_datetime
import config
from datetime import timezone
from datetime import datetime

Base = declarative_base()
class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	playfab_id = Column(String, unique=True)
	discord_id = Column(String)
	nickname = Column(String)
	is_admin = Column(Boolean)
	last_seen = Column(DateTime)
	total_playtime = Column(Float)

	actions = relationship("AdminAction",
		back_populates = 'admin', foreign_keys = 'AdminAction.admin_id')
	infractions = relationship("AdminAction",
		back_populates = 'target', foreign_keys = 'AdminAction.target_id')

	def __repr__(self):
		return f'<User(playfabid={self.playfab_id}, nickname={self.nickname})>'


class AdminAction(Base):
	__tablename__ = 'adminactions'
	id = Column(Integer, primary_key=True)
	admin_id = Column(Integer, ForeignKey('users.id'))
	target_id = Column(Integer, ForeignKey('users.id'))
	action_type = Column(String)
	time = Column(DateTime)
	duration = Column(Integer)
	reason = Column(String)

	admin = relationship('User', back_populates='actions',
		foreign_keys = [admin_id])
	target = relationship('User', back_populates='infractions',
		foreign_keys = [target_id])

	def __repr__(self):
		return f'<AdminAction(target={self.target}, type={self.action_type})>'


class DB:
	def __init__(self, db_url=''):
		self.engine = create_async_engine(db_url,
								echo=True, future=True)

		self.Session = sessionmaker(
			self.engine, expire_on_commit=False, class_=AsyncSession)

	async def reset(self):
		async with self.engine.begin() as conn:
			#await conn.run_sync(Base.metadata.drop_all)
			await conn.run_sync(Base.metadata.create_all)

	async def handle_msg(self, logmsg, msgtype, data, session):
		"""Convert a message from logparse into an AdminAction and create
		users as needed."""


		handled_types = ('ban', 'kick', 'unban', 'mute', 'unmute',
			'cancelvotekick')
		if msgtype not in handled_types: return None

		action = AdminAction()
		# set the time
		action.time = timestamp_to_datetime(data['timestamp'])
		# set the action type
		action.action_type = msgtype
		# search for admin with playfabid
		res = await session.execute(
			sa.select(User)
			.options(selectinload(User.infractions))
			.options(selectinload(User.actions))
			.filter_by(playfab_id=data['adm_playfabid']))
		admin = res.scalars().first()
		if not admin:
			# create the admin user
			admin = User(
				playfab_id = data['adm_playfabid'],
				nickname = data['adm_name'],
				last_seen = datetime.utcnow(),#datetime.now(timezone.utc),
				is_admin = True,
				total_playtime = 0)
			session.add(admin)
		# set the admin
		action.admin = admin
		# search for target with playfabid
		res = await session.execute(
			sa.select(User)
			.options(selectinload(User.infractions))
			.options(selectinload(User.actions))
			.filter_by(playfab_id=data['plyr_playfabid']))
		target = res.scalars().first()
		if not target:
			# create the target user
			target = User(
				playfab_id = data['plyr_playfabid'],
				last_seen = datetime.utcnow(),#datetime.now(timezone.utc),
				is_admin = False,
				total_playtime = 0)
			session.add(target)
		# set the target
		action.target = target
		try:
			# set the duration
			action.duration = int(data['duration'])
		except KeyError:
			pass
		try:
			# set the reason
			action.reason = data['reason']
		except KeyError:
			pass
		session.add(action)

	async def get_discordid_from_playfabid(self, playfabid):
		async with self.Session() as session:
			res = await session.execute(
				sa.select(User)
				.options(selectinload(User.infractions))
				.options(selectinload(User.actions))
				.filter_by(playfab_id=playfabid))
			user = res.scalars().first()
			if user:
				return user.discord_id

