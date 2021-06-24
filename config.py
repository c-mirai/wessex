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

import configparser
import json

config = configparser.ConfigParser()
config.read("config/config.ini")

log_chat = config.getboolean("discord","log_chat")
log_ban = config.getboolean("discord","log_ban")
log_kick = config.getboolean("discord","log_kick")
log_unban = config.getboolean("discord","log_unban")
log_mute = config.getboolean("discord","log_mute")
log_unmute = config.getboolean("discord","log_unmute")

chat_channelid = int(config["discord"]["chat_channelid"])
ban_channelid = int(config["discord"]["ban_channelid"])
kick_channelid = int(config["discord"]["kick_channelid"])
unban_channelid = int(config["discord"]["unban_channelid"])
mute_channelid = int(config["discord"]["kick_channelid"])
unmute_channelid = int(config["discord"]["unban_channelid"])

#return all the necessary info to download the logfile
def get_ftp_config():
	return (config['ftp']['host'],
			int(config['ftp']['port']),
			config['ftp']['username'],
			config['ftp']['password'],
			config['ftp']['logpath'])

def read_array(key, val):
	return json.loads(config[key][val])

def main():
	print(config['ftp']['host'])

if __name__ == '__main__':
	main()

