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