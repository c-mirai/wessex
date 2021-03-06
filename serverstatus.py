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

"""Handles the tracking of server stats"""
import time
import calendar
import logparse
from texttable import Texttable
import logging

logging.basicConfig(level=logging.INFO)

def format_time(t):
	"""Take a number of seconds and return a string representing it in human-readable form, with the highest increment being days."""
	#this could be improved with a dynamic "and" position but by golly it's good enough
	days = int(t // 86400)
	hours = int(t // 3600 % 24)
	minutes = int(t // 60 % 60)
	seconds = int(t % 60)
	f = ""
	comma = False
	if days:
		f = str(days) + " day"
		if days > 1:
			f += "s"
		comma = True
	if hours:
		if comma:
			f = f + ", "
		f = f + str(hours) + " hour"
		if hours > 1:
			f += "s"
		comma = True
	if minutes:
		if comma:
			f = f + ", "
		f = f + str(minutes) + " minute"
		if minutes > 1:
			f += "s"
		comma = True
	if seconds:
		if comma:
			f = f + " and "
		f = f + str(seconds) + " second"
		if seconds > 1:
			f += "s"
	if not f:
		f = "0 seconds"
	return f

class ServerStatus:
	def __init__(self):
		self.player_count = 0
		self.max_players = 0 #
		self.reserved_slots = 0
		#format {playfabid: [name, is_admin]}
		self.player_list = {}
		self.mapname = ""
		self.gamemode = ""
		self.start_time = 0
		self.server_name = "" #
		self.server_ip = "" #
		self.game_port = 0 #
		self.mods = [] #unimplemented
		self._initialized = False
		# self.messages_handled = 0
	async def handle_msg(self, msg, msgtype, match=None):
		"""Handle a single log string from logparse."""

		# self.messages_handled += 1
		# if not self.messages_handled % 100:
		# 	logging.info(f'Messages handled: {self.messages_handled}')
		if msgtype == "update":
			res = logparse.format_update(match)
			names = ("timestamp", "mapname", "mode", "playernum", "reservedslots")
			(timestamp, mapname, mode, playernum, reservedslots) = (res[k] for k in names)
			self.mapname = mapname
			self.gamemode = mode
			self.player_count = playernum
			self.reserved_slots = reservedslots
		elif msgtype == "plyrjoin":
			res = logparse.format_plyrjoin(match)
			names = ("timestamp", "plyr_name", "plyr_playfabid")
			(timestamp, name, pfid) = (res[k] for k in names)
			self.player_list[pfid] = [name, False]
		elif msgtype == "admjoin":
			res = logparse.format_admjoin(match)
			names = ("timestamp", "plyr_name", "plyr_playfabid")
			(timestamp, name, pfid) = (res[k] for k in names)
			if self.player_list.get(pfid):
				#set the is_admin flag
				self.player_list[pfid][1] = True
		elif msgtype == "plyrleave":
			res = logparse.format_plyrleave(match)
			names = ("timestamp", "plyr_addr", "plyr_playfabid")
			(timestamp, addr, pfid) = (res[k] for k in names)
			self.player_list.pop(pfid, None)

	def status(self):
		"""Output server status."""
		time = format_time(self.get_uptime())
		table = Texttable()
		table.set_cols_align(["r", "l"])
		table.set_header_align(["r", "l"])
		table.add_rows([
			["Players:", self.player_count],
			["Map:", self.mapname],
			["Gamemode:", self.gamemode],
			["Uptime:", time],
		])
		table.set_deco(0)
		
		#s = f"Players: {self.player_count}\nMap: {self.mapname}\nGamemode: {self.gamemode}\nUptime: {time}"
		return f"```{table.draw()}```"

	def playerlist(self):
		"""Output list of players"""
		table = Texttable()
		table.set_deco(0)
		table.set_cols_align(["l", "l"])
		list = ""
		for pfid in self.player_list:
			list = list + f"{self.player_list[pfid][0]} ({pfid})\n"
			table.add_row([f"({pfid})", self.player_list[pfid][0]])
		if list:
			#get rid of the trailing \n
			return table.draw()
			#return list[:-1]

		return "No players currently playing." #no players

	async def force_init(self, data, db):
		"""Initialize anything requiring access to the full log file."""
		#get the date string
		start = data[16:data.find('\r')]
		print(start)
		#convert to time
		#eg. 01/09/21 15:46:46
		self.start_time = calendar.timegm(time.strptime(start, "%m/%d/%y %H:%M:%S"))
		#get server registered info
		match =  logparse.register_pattern.search(data)
		info = logparse.format_register(match)
		self.server_name 	= info["server_name"]
		self.max_players 	= int(info["max_players"])
		self.server_ip 		= info["ip"]
		self.game_port		= int(info["game_port"])
		await logparse.parse_lines(data, db, self.handle_msg, False)

	async def init_from_log(self, data, db):
		"""Wrapper for force_init, only able to be called once.

		Returns True if this is the first time init_from_log has been called."""
		if not self._initialized:
			await self.force_init(data, db)
			self._initialized = True
			return True
		return False

	def get_uptime(self):
		"""Return the amount of time the server has been running."""
		return time.time() - self.start_time - 60*60*5 #ghetto timezone handling
		pass

	def get_uptime_readable(self):
		"""Take a time in seconds and return a human-readable representation."""
		return format_time(self.get_uptime())

async def main():

	import mydb
	ss = ServerStatus()
	DB = mydb.db()
	import fileio
	data = fileio.read_binary("Mordhau.log")
	await ss.init_from_log(data, DB)
	#await logparse.parse_lines(data, DB, ss.handle_msg)
	#print("Server uptime: {}.".format(format_time(ss.get_uptime())))
	print(ss.status())
	print(ss.playerlist())

if __name__ == '__main__':
	import asyncio
	asyncio.run(main())