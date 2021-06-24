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