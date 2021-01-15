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
		global __name__
		atexit.register(self._save_queue)
		self._msg_ratelimit = float(config.config['discord']['msg_ratelimit'])
		self._msg_queue = asyncio.PriorityQueue()
		self._msg_queue_loaded = asyncio.Event()
		#this event signals when the message queue has been loaded and is able to start taking new messages
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

	async def _load_queue(self):
		tmp_queue = fileio.load_queue()
		new_queue = asyncio.PriorityQueue()
		#we need to convert channel ids into channel objects
		Item = None
		while 1:
			try:
				item = tmp_queue.get_nowait()
			except asyncio.QueueEmpty:
				break
			print(repr(item))
			print(item[0])
			(priority, (msg, channelid)) = item
			item = (int(priority), (msg, self.get_channel(channelid)))
			await new_queue.put(item)
		return new_queue

	async def _process_msg_loop(self):
		#await self.wait_until_ready()
		#wait for the message queue loaded event
		await self._msg_queue_loaded.wait()
		while not self.is_closed():
			msg = await self._msg_queue.get()
			print("sending {}".format(msg[1][0]))
			await msg[1][1].send(msg[1][0])
			qsize = self._msg_queue.qsize()
			if qsize % 10 == 1:
				#print qsize every 10
				print(f"Queue size: {qsize}")
			self._msg_queue.task_done()
			await asyncio.sleep(self._msg_ratelimit)

	def set_loop(self, loop):
		self.bg_loop = self.loop.create_task(loop(self))

	async def on_ready(self):
		#this needs to be done here so that get_channel can resolve the channel ids
		self._msg_queue = await self._load_queue()
		self._msg_queue_loaded.set()
		client = self
		#test
		channel = client.get_channel(798198029919322122)
		print(f"{client.user} has connected to Discord!")
		print(f"{client.user} is connected to the following guilds:")
		for guild in client.guilds:
			print(f"{guild.name} (id: {guild.id})")
		#members = '\n - '.join([f"{member.name} ({member.id})"  for member in guild.members])
		#print(f'Guild Members:\n - {members}')

		#meme section
		#channel = self.get_channel(798277528916590662)
		#await channel.send("smh")

	async def on_message(self, message):
		client = self
		if message.author == client.user:
			return

		print(type(message))
		print(message.content)

	async def send_msg(self, msg, channel, priority=2, msgtype=""):
		"""Adds a message to the message queue, to be sent at a rate that complies with discord's rate limit."""
		#print((priority, (msg, channel)))
		await self._msg_queue.put((priority, (msg, channel)))

async def main_loop(client):
	#await client.wait_until_ready()
	await client._msg_queue_loaded.wait()
	#while not client.is_closed():
	#print(client._msg_queue)
	test_channel = client.get_channel(798198029919322122)
	import random
	for i in range(10):
		await client.send_msg(f"test{random.randint(1,100)}", test_channel)
	print("test messages sent")


def main():
	client = MyClient(intents=intents)
	client.set_loop(main_loop)
	client.run(TOKEN)

if __name__ == '__main__':
	main()
