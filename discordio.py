# bot.py
import config
import discord
import time
import logging
import asyncio
import fileio
import sys
import datetime
import dateutil.tz
#import serverstatus
from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logfile = config.config['discord']['logfile']
handler = logging.FileHandler(filename=logfile, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
#intents.members = True

TOKEN = config.config["discord"]["token"]
#GUILDS = config.read_array("discord.guilds","guilds")

class MyClient(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		#Discord message rate limit (seconds per message)
		import atexit
		global __name__
		atexit.register(self._save_queue)
		self._msg_ratelimit = float(config.config['discord']['msg_ratelimit'])
		self._char_limit = int(config.config['discord']['char_limit'])
		self._chat_batch = ""
		self._chat_channel = 0
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
			if self._chat_batch:
				#print(f"sending chat batch:{self._chat_batch}")
				await self.send_msg(self._chat_batch, self._chat_channel, int(config.config['discord']['chat_priority']))
				self._chat_batch = ""

			try:
				msg = self._msg_queue.get_nowait()
				#print("sending {}".format(msg[1][0]))
				await msg[1][1].send(msg[1][0])
				qsize = self._msg_queue.qsize()
				if qsize % 10 == 1:
					#print qsize every 10
					print(f"Queue size: {qsize}")
				self._msg_queue.task_done()
			except asyncio.QueueEmpty:
				#print("queue empty")
				pass
			except OSError as err:
				print("OS error: {0}".format(err))
				#connection reset by peer?
			except discord.errors.HTTPException as httperr:
				print("Http err: {}\n{}\n Length: {}".format(httperr, msg[1][0], len(msg[1][0])))

			await asyncio.sleep(self._msg_ratelimit)

	def set_loop(self, loop):
		self.bg_loop = self.loop.create_task(loop(self))

	async def on_ready(self):
		#this needs to be done here so that get_channel can resolve the channel ids
		self._chat_channel = self.get_channel(int(config.config['discord']['chat_channelid']))
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

	async def send_msg(self, msg, channel, priority=2, msgtype=""):
		"""Adds a message to the message queue, to be sent at a rate that complies with discord's rate limit."""
		#print((priority, (msg, channel)))
		if msgtype == "chat":
			msg = discord.utils.escape_markdown(msg)
			msg = discord.utils.escape_mentions(msg)
			#implement chat batching
			if len(self._chat_batch) + len(msg) > self._char_limit - 1: #-1 to account for the \n added
				#dispatch the batch
				await self._msg_queue.put((priority, (self._chat_batch, channel)))
				self._chat_batch = msg
			else:
				#add to the batch
				#print(f"Adding {msg} to chat batch")
				self._chat_batch += "\n" + msg
		else:
			await self._msg_queue.put((priority, (msg, channel)))

	def _format_status_embed(self, ss):
		playerlist = ss.playerlist()
		embed = (discord.Embed(title="Server Status", color=0x773300, timestamp=datetime.datetime.now(dateutil.tz.gettz()))
			.set_footer(text="Updates every 5 minutes")
			#.set_author(name="Server Status")
			.add_field(name=ss.server_name, value=f"{ss.server_ip}:{ss.game_port}", inline=False)
			.add_field(name="Player Count", value=f"{ss.player_count}/{ss.max_players}", inline=False)
			.add_field(name="Map", value=ss.mapname, inline=False)
			.add_field(name="Gamemode", value=ss.gamemode, inline=False)
			.add_field(name="Uptime", value=ss.get_uptime_readable(), inline=False)
			.add_field(name="Player List", value=playerlist, inline=False)
			)
		return embed

	async def update_status(self, ss, channel_id=801132836777099294):
		#guild = self.get_guild(guild_id)
		channel = self.get_channel(channel_id)
		messages = await channel.history(limit=2).flatten()
		status_embed = self._format_status_embed(ss)
		if len(messages):
			await messages[0].edit(embed=status_embed)
		else:
			await channel.send(embed=status_embed)

		if len(messages) > 1:
			pass

async def main_loop(client):
	#await client.wait_until_ready()
	await client._msg_queue_loaded.wait()
	#while not client.is_closed():
	#print(client._msg_queue)
	from datetime import datetime
	from dateutil import tz
	test_channel = client.get_channel(798198029919322122)
	test_message = await test_channel.fetch_message(801128435308953640)
	embed = (discord.Embed(title="Server Status", color=0x663300, timestamp=datetime.now(tz.gettz()))
			#.set_footer(text="Last Updated")
			#.set_author(name="Server Status")
			.add_field(name="Player count", value="45", inline=False)
			.add_field(name="Map", value="Contraband", inline=False)
			.add_field(name="Gamemode", value="Deathmatch", inline=False)
			.add_field(name="Uptime", value="5 seconds", inline=False)
			)
	await test_message.edit(embed=embed)


def main():
	client = MyClient(intents=intents, command_prefix="$")
	client.set_loop(main_loop)
	client.run(TOKEN)

if __name__ == '__main__':
	main()
