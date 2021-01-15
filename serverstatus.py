"""Handles the tracking of server stats"""
import time
import calendar
import logparse

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
	if seconds:
		if comma:
			f = f + " and "
		f = f + str(seconds) + " second"
		if seconds > 1:
			f += "s"
	return f

class ServerStatus:
	def __init__(self):
		self.player_count = 0
		self.reserved_slots = 0
		self.player_list = []
		self.mapname = ""
		self.gamemode = ""
		self.start_time = 0
		self._initialized = False
	async def handle_msg(self, msg, msgtype, match=None):
		"""Handle a single log string from logparse."""
		if msgtype == "update":
			(timestamp, mapname, mode, playernum, reservedslots) = logparse.format_update(match)
			self.mapname = mapname
			self.gamemode = mode
			self.player_count = playernum
			self.reserved_slots = reservedslots
		pass

	def str(self):
		"""Output relevant server info."""
		time = format_time(self.get_uptime())
		s = f"Players: {self.player_count}\nMap: {self.mapname}\nGamemode: {self.gamemode}\nUptime: {time}"
		return s

	async def force_init(self, data, db):
		"""Initialize anything requiring access to the full log file."""
		#get the date string
		start = data[18:data.find("\n")]
		#convert to time
		#eg. 01/09/21 15:46:46
		self.start_time = calendar.timegm(time.strptime(start, "%m/%d/%y %H:%M:%S"))
		await logparse.parse_lines(data, db, self.handle_msg)

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
		return time.time() - self.start_time
		pass

async def main():
	import mydb
	ss = ServerStatus()
	DB = mydb.db()
	import fileio
	data = fileio.read("Mordhau.log")
	await ss.init_from_log(data, DB)
	#await logparse.parse_lines(data, DB, ss.handle_msg)
	#print("Server uptime: {}.".format(format_time(ss.get_uptime())))
	print(ss.str())

if __name__ == '__main__':
	import asyncio
	asyncio.run(main())