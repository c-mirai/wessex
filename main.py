import logparse
import ftp
import aftp
import config
import fileio
import time
import asyncio
import discordio
import mydb
import sqlitedb
import serverstatus
import command
import logging

logging.basicConfig(level=logging.INFO)

async def main_loop(client):
	
	DB = sqlitedb.db()
	SS = serverstatus.ServerStatus()
	#await client.wait_until_ready()
	await client._msg_queue_loaded.wait()
	#add commands
	client.add_cog(command.Status(client, SS))


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
		async def handle_msg(*args):
			"""Handle messages.

			logmsg 	- readable form of the message
			msgtype - message type
			match 	- regex match of the message"""
			# await SS.handle_msg(*args)
			# await client.handle_msg(*args)
			await asyncio.gather(
				SS.handle_msg(*args),
				client.handle_msg(*args),
			)

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