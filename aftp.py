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

import asyncio
import aioftp
import logging
import config

async def get_remote_file_binary(host, port, usr, pwd, filepath):
	"""Asynchronously download a file and return its binary contents."""
	client = aioftp.Client(read_speed_limit=int(config.config["ftp"]["throttle"]))
	logging.info(f"Connecting to {host}:{port}.")
	await client.connect(host, port)
	logging.info(f"Logging in.")
	await client.login(usr, pwd)
	stat = await client.stat(filepath)
	logging.debug(stat)
	data = bytearray()
	pc = 0
	async with client.download_stream(filepath) as stream:
		async for block in stream.iter_by_block():
			data += block
			percent = len(data)/int(stat["size"])
			if pc + percent > .05:
				logging.info(f"File transfer {percent*100:.2f}% complete.")
				pc -= .05

	logging.info(f"Closing connection.")
	await client.quit()
	logging.info(f"Downloaded {len(data)} bytes.")
	return data

async def amain():
	logging.basicConfig(level=logging.DEBUG)
	import config
	data = await get_remote_file_binary(*config.get_ftp_config())
	#print(data)

def main():
	logging.basicConfig(level=logging.DEBUG)
	asyncio.run(amain())

if __name__ == '__main__':
	main()
