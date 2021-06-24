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

import config
import json

#this may be upgraded to an actual database in the future

class db:
	def __init__(self):
		self._admins = {}
		self.load_admins()
	def load_admins(self):
		with open(config.config['db']['admins'], 'r') as fp:
			self._admins = json.load(fp)
		print("Loaded admins.")
	async def get_discordid_from_playfabid(self, playfabid):
		#for efficiency we've indexed by playfabid
		#not that it matters
		discordid = ""
		try:
			discordid = self._admins[playfabid]["discordid"]
		except KeyError:
			return ""
		return discordid


def main():
	mydb = db()
	assert mydb.get_discordid_from_playfabid("6EAAAD38A6BC0D8D") == "513957278269833236"

if __name__ == '__main__':
	main()