import logparse
import ftp
import config
import fileio
import time
import asyncio
import discordio

async def main_loop(client):
	await client.wait_until_ready()

	#config structures (for convenience)
	channels = {
		"chat": client.get_channel(config.chat_channelid),
		"ban": client.get_channel(config.ban_channelid),
		"kick": client.get_channel(config.kick_channelid),
		"unban": client.get_channel(config.unban_channelid),
	}
	channel_flags = {
		"chat": config.log_chat,
		"ban": config.log_ban,
		"kick": config.log_kick,
		"unban": config.log_unban,
	}
	msgtype_priorities = {
		"chat": config.config["discord"]["chat_priority"],
		"ban": config.config["discord"]["ban_priority"],
		"kick": config.config["discord"]["kick_priority"],
		"unban": config.config["discord"]["unban_priority"],
	}

	while not client.is_closed():
		#retrieve the log file from remote server
		(host, port, usr, pwd, filepath) = config.get_ftp_config()
		data = ftp.get_remote_file_text(host, port, usr, pwd, filepath)

		#update local copy and return its previous contents
		fname = config.config['fileio']['localcopy']
		old_data = fileio.update(fname, data)

		#find the new part of the log
		print("Finding new log entries.")
		new_data = logparse.log_diff(old_data, data)

		print("New data length: {} bytes".format(len(new_data)))
		async def send_logmsg(logmsg, msgtype):
			"""Sends a log message to discord depending on the type"""
			nonlocal client
			if channel_flags[msgtype]:
				#printf("waiting")
				await client.send_msg(logmsg, channels[msgtype],msgtype_priorities[msgtype])

		await logparse.parse_lines(new_data, send_logmsg)
		#wait
		interval = int(config.config['time']['interval'])
		print("Waiting {} seconds".format(interval))
		#await channel.send("Log finished processing.")
		await asyncio.sleep(interval)

client = discordio.MyClient(intents=discordio.intents)
client.set_loop(main_loop)
client.run(discordio.TOKEN)