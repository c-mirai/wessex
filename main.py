import logparse
import ftp
import aftp
import config
import fileio
import time
import asyncio
import discordio
import mydb
import serverstatus
import command
import logging

logging.basicConfig(level=logging.INFO)

async def main_loop(client):
	
	DB = mydb.db()
	SS = serverstatus.ServerStatus()
	#await client.wait_until_ready()
	await client._msg_queue_loaded.wait()
	#add commands
	client.add_cog(command.Status(client, SS))

	#config structures (for convenience)
	channels = {
		"chat": client.get_channel(config.chat_channelid),
		"ban": client.get_channel(config.ban_channelid),
		"kick": client.get_channel(config.kick_channelid),
		"unban": client.get_channel(config.unban_channelid),
		"mute": client.get_channel(config.mute_channelid),
		"unmute": client.get_channel(config.unmute_channelid),
	}
	channel_flags = {
		"chat": config.log_chat,
		"ban": config.log_ban,
		"kick": config.log_kick,
		"unban": config.log_unban,
		"update": False,
		"plyrjoin": False,
		"admjoin": False,
		"plyrleave": False,
		"mute": config.log_mute,
		"unmute": config.log_unmute,
	}
	msgtype_priorities = {
		"chat": int(config.config["discord"]["chat_priority"]),
		"ban": int(config.config["discord"]["ban_priority"]),
		"kick": int(config.config["discord"]["kick_priority"]),
		"unban": int(config.config["discord"]["unban_priority"]),
		"mute": int(config.config["discord"]["mute_priority"]),
		"unmute": int(config.config["discord"]["unmute_priority"]),
	}
	fname = config.config['fileio']['localcopy']
	while not client.is_closed():
		(host, port, usr, pwd, filepath) = config.get_ftp_config()
		data = await aftp.get_remote_file_binary(host, port, usr, pwd, filepath)
		#update local copy and return its previous contents
		old_data = fileio.update_binary(fname, data)
		#convert to text
		data = data.decode()
		old_data = old_data.decode()
		#find the new part of the log
		print("Finding new log entries.")
		new_data = logparse.log_diff(old_data, data)
		print("New data length: {} bytes".format(len(new_data)))
		#init server status
		if old_data:
			#initialize from the old section of the log file.
			await SS.init_from_log(old_data, DB)
		else:
			#log file is new, completely reinitialize.
			await SS.force_init(new_data, DB)
		async def handle_msg(logmsg, msgtype, match):
			"""Sends a log message to discord depending on the type"""
			await SS.handle_msg(logmsg, msgtype, match)
			#todo: extend the above format to discordio with a client.handle_logmsg method
			nonlocal client
			if channel_flags[msgtype]:
				await client.send_msg(logmsg, channels[msgtype], msgtype_priorities[msgtype], msgtype)

		await logparse.parse_lines(new_data, DB, handle_msg)
		#update status
		print("Updating status.")
		await client.update_status(SS)
		#wait
		interval = int(config.config['time']['interval'])
		print("Waiting {} seconds".format(interval))
		await asyncio.sleep(interval)

client = discordio.MyClient(intents=discordio.intents, command_prefix="$")

# @client.command()
# async def test(ctx, arg):
# 	print(arg)
# 	await ctx.send(arg)

client.set_loop(main_loop)
client.run(discordio.TOKEN)