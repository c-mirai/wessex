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