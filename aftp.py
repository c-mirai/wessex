import asyncio
import aioftp
import logging

async def get_remote_file_binary(host, port, usr, pwd, filepath):
	client = aioftp.Client()
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
