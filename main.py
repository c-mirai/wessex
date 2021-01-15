import logparse
import ftp
import config
import fileio
import time
import asyncio
import discordio
import mydb
import serverstatus

async def main_loop(client):
	DB = mydb.db()
	SS = serverstatus.ServerStatus()

	#await client.wait_until_ready()
	await client._msg_queue_loaded.wait()

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
		"chat": int(config.config["discord"]["chat_priority"]),
		"ban": int(config.config["discord"]["ban_priority"]),
		"kick": int(config.config["discord"]["kick_priority"]),
		"unban": int(config.config["discord"]["unban_priority"]),
	}
	fname = config.config['fileio']['localcopy']
	while not client.is_closed():
		(host, port, usr, pwd, filepath) = config.get_ftp_config()
		data = ftp.get_remote_file_text(host, port, usr, pwd, filepath)
		#update local copy and return its previous contents
		old_data = fileio.update(fname, data)
		#find the new part of the log
		print("Finding new log entries.")
		new_data = logparse.log_diff(old_data, data)
		print("New data length: {} bytes".format(len(new_data)))
		#init server status
		if old_data:
			#initialize from the old section of the log file.
			await ss.init_from_log(old_data)
		else:
			#log file is new, completely reinitialize.
			await ss.force_init(new_data)
		async def handle_logmsg(logmsg, msgtype, match):
			"""Sends a log message to discord depending on the type"""
			ss.handle_logmsg(logmsg, msgtype, match)
			#todo: extend the above format to discordio with a client.handle_logmsg method
			nonlocal client
			if channel_flags[msgtype]:
				#printf("waiting")
				await client.send_msg(logmsg, channels[msgtype], msgtype_priorities[msgtype], msgtype)

		await logparse.parse_lines(new_data, DB, handle_logmsg)
		#wait
		interval = int(config.config['time']['interval'])
		print("Waiting {} seconds".format(interval))
		#await channel.send("Log finished processing.")
		await asyncio.sleep(interval)

client = discordio.MyClient(intents=discordio.intents)
client.set_loop(main_loop)
client.run(discordio.TOKEN)