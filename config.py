import configparser
import json

config = configparser.ConfigParser()
config.read("config/config.ini")

log_chat = config.getboolean("discord","log_chat")
log_ban = config.getboolean("discord","log_ban")
log_kick = config.getboolean("discord","log_kick")
log_unban = config.getboolean("discord","log_unban")

chat_channelid = int(config["discord"]["chat_channelid"])
ban_channelid = int(config["discord"]["ban_channelid"])
kick_channelid = int(config["discord"]["kick_channelid"])
unban_channelid = int(config["discord"]["unban_channelid"])

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

