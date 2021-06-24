from ftplib import FTP
import sys
import logging

def get_remote_file_text(host, port, usr, pwd, filepath):
	data = ""
	ftp = FTP()
	try:
		print(ftp.connect(host, port))
		print(ftp.login(usr, pwd))
	except TimeoutError:
		logging.warning(f"TimeoutError connecting to {host}:{port}")
		pass
	except:
		logging.critical("Unexpected error in ftp")
		raise
	def read_line(line):
		nonlocal data
		data += line + '\n'
	#download the file
	try:
		print(ftp.retrlines('RETR {}'.format(filepath),read_line))
	except:
		print("Unexpected error:", sys.exc_info()[0])
		raise
	print("Transfer size: {} bytes".format(len(data)))
	print(ftp.quit())
	return data

def get_remote_file_binary(host, port, usr, pwd, filepath):
	ftp = FTP()
	data = bytearray()
	try:
		print(ftp.connect(host, port))
		print(ftp.login(usr, pwd))
	except TimeoutError:
		logging.warning(f"TimeoutError connecting to {host}:{port}")
		pass
	except:
		logging.critical("Unexpected error in ftp")
		raise
	def read_block(block):
		nonlocal data
		data += block
		pass
	try:
		print(ftp.retrbinary('RETR {}'.format(filepath),read_block))
	except:
		print("Unexpected error:", sys.exc_info()[0])
		raise
	print("Transfer size: {} bytes".format(len(data)))
	print(ftp.quit())
	return data

def main():
	import config
	data = get_remote_file_binary(*config.get_ftp_config())
	print(data)

if __name__ == '__main__':
	main()