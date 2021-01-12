# bot.py
import config
import discord
import time
import logging
import asyncio
import fileio


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logfile = config.config['discord']['logfile']
handler = logging.FileHandler(filename=logfile, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True

TOKEN = config.config["discord"]["token"]
#GUILDS = config.read_array("discord.guilds","guilds")

class MyClient(discord.Client):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		#Discord message rate limit (seconds per message)
		import atexit
		atexit.register(self._save_queue)
		self._msg_ratelimit = 60/120
		self._msg_queue = self._load_queue()
		#load_queue loads channels as ids. we have to convert them to channels
		self.loop.create_task(self._process_msg_loop())

	def _save_queue(self):
		tmp_queue = asyncio.Queue()
		#before we can call fileio.save_queue, we need to convert the channel objects into channel ids
		while 1:
			try:
				item = self._msg_queue.get_nowait()
				(priority, (msg, channel)) = item
				item = (priority, (msg, channel.id))
				tmp_queue.put_nowait(item)
			except asyncio.QueueEmpty:
				break
		fileio.save_queue(tmp_queue)

	def _load_queue(self):
		tmp_queue = fileio.load_queue()
		new_queue = asyncio.PriorityQueue()
		#we need to convert channel ids into channel objects
		while 1:
			try:
				item = tmp_queue.get_nowait()
				(priority, (msg, channelid)) = item
				item = (priority, (msg, self.get_channel(channelid)))
				new_queue.put_nowait(item)
			except asyncio.QueueEmpty:
				break
		return new_queue

	async def _process_msg_loop(self):
		await self.wait_until_ready()

		while not self.is_closed():
			msg = await self._msg_queue.get()
			await msg[1][1].send(msg[1][0])
			self._msg_queue.task_done()
			await asyncio.sleep(self._msg_ratelimit)

	def set_loop(self, loop):
		self.bg_loop = self.loop.create_task(loop(self))

	async def on_ready(self):
		client = self
		#test
		channel = client.get_channel(798198029919322122)
		print(f"{client.user} has connected to Discord!")
		print(f"{client.user} is connected to the following guilds:")
		for guild in client.guilds:
			print(f"{guild.name} (id: {guild.id})")
		members = '\n - '.join([f"{member.name} ({member.id})"  for member in guild.members])
		print(f'Guild Members:\n - {members}')

		#meme section
		#channel = self.get_channel(798277528916590662)
		#await channel.send("smh")

	async def on_message(self, message):
		client = self
		if message.author == client.user:
			return

		print(type(message))
		print(message.content)

	async def send_msg(self, msg, channel, priority=2):
		"""Adds a message to the message queue, to be sent at a rate that complies with discord's rate limit."""
		await self._msg_queue.put((priority, (msg,channel)))


def main():
	client = MyClient(intents=intents)
	client.run(TOKEN)

if __name__ == '__main__':
	main()
