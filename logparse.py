import re
import io
import datetime

timestamp_pattern 	= re.compile("\[\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3}\]")
microsecond_pattern = re.compile(":(\d{3})\]")
ban_pattern 		= re.compile("\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) banned player (.*) \(Duration: (\d*), Reason: (.*)\)(\n|$)")
kick_pattern 		= re.compile("\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) kicked player (.*) \(Reason: (.*)\)(\n|$)")
kickban_pattern 	= re.compile("\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauGameSession: Kicked player (.*) \((.*)\), reason: (.*)(\n|$)")
unban_pattern 		= re.compile("\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) unbanned player (.*)(\n|$)")
chat_pattern 		= re.compile("\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogGameMode: Display: \((.*)\) (.*), (.*): \"(.*)\"(\n|$)")
update_pattern 		= re.compile("\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogPlayFabAPI: Verbose: UpdateGameServer \(Map: (.*), GameMode: (.*), Players: (.*), ReservedSlots: (.*)\)(\n|$)")

#calculates the novel part of the new log file
def log_diff(old_data, data):
	#passthrough if no old_data
	if not old_data:
		print("No old data found. All data is new.")
		return data

	global timestamp_pattern
	new_data = ""
	#find the first timestamp in each log
	t1 = timestamp_pattern.search(old_data).group(0)
	t2 = timestamp_pattern.search(data).group(0)
	print("Old timestamp: {}\nNew timestamp: {}".format(t1,t2))
	if t1 == t2:
		print("Head match detected; calculating new data.")
		#lets say the old log is 100 bytes and the new one is 130 bytes.
		#we assume the first 100 bytes are identical and just grab the final 30 bytes
		old_size = len(old_data)
		new_data = data[old_size:]
	else:
		print("Head mismatch detected; all data is new.")
		new_data = data
	return new_data

def timestamp_to_datetime(timestamp):
	#[2021.01.09-22.17.01:079]
	#"%Y.%m.%d-%H.%M.%S:%f"
	#dt = datetime.datetime()
	dt = datetime.datetime.strptime(timestamp, "%Y.%m.%d-%H.%M.%S:%f")
	return dt

#tries to associate a player name with a playfabid
#certain playernames or log truncation can cause this to return incorrect results
def guess_name(data, playfabid):
	guessname_pattern = re.compile("(P|p)layer (.*) \({}\)".format(playfabid))
	match = guessname_pattern.search(data)
	if match:
		return match.group(2)
	return ""

def format_ban(match):
	timestamp	 		= match.group(1)
	adm_name 			= match.group(2)
	adm_playfabid 		= match.group(3)
	plyr_playfabid 		= match.group(4)
	duration 			= match.group(5)
	reason				= match.group(6)
	return (timestamp, adm_name, adm_playfabid, plyr_playfabid, duration, reason)

def format_kick(match):
	timestamp	 		= match.group(1)
	adm_name 			= match.group(2)
	adm_playfabid 		= match.group(3)
	plyr_playfabid 		= match.group(4)
	reason				= match.group(5)
	return (timestamp, adm_name, adm_playfabid, plyr_playfabid, reason)

def format_unban(match):
	timestamp	 		= match.group(1)
	adm_name 			= match.group(2)
	adm_playfabid 		= match.group(3)
	plyr_playfabid 		= match.group(4)
	return (timestamp, adm_name, adm_playfabid, plyr_playfabid)

def format_chat(match):
	timestamp	 		= match.group(1)
	mode 				= match.group(2)
	name 				= match.group(3)
	plyr_playfabid		= match.group(4)
	msg 				= match.group(5)
	return (timestamp, mode, name, plyr_playfabid, msg)

def format_update(match):
	timestamp 			= match.group(1)
	mapname				= match.group(2)
	mode 				= match.group(3)
	playernum 			= match.group(4)
	reservedslots 		= match.group(5)
	return (timestamp, mapname, mode, playernum, reservedslots)

def match_ban(line):
	return ban_pattern.match(line)

def match_kick(line):
	return kick_pattern.match(line)

def match_unban(line):
	return unban_pattern.match(line)

def match_chat(line):
	return chat_pattern.match(line)

def match_update(line):
	return update_pattern.match(line)

async def parse_lines(data, db, callback=None):
	"""loops through every line in the log and determines its type, formats the log msg then calls callback on it

	data - the log data to loop over, string
	db - a mydb object to assist with playfabid->discordid resoltion
	callback - a function that gets called on each log message. takes two arguments, logmsg string and type string"""
	buf = io.StringIO(data)
	line = "True"
	match = None
	printing = False
	while(line):
		line = buf.readline()
		if match := match_chat(line):
			res = format_chat(match)
			(timestamp, mode, name, plyr_playfabid, msg) = res
			logmsg = "[{}] ({}) {} ({}): {}".format(timestamp, mode, name, plyr_playfabid, msg)
			printing and print(logmsg)
			callback and await callback(logmsg, "chat")
			continue
		if match := match_ban(line):
			res = format_ban(match)
			(timestamp, adm_name, adm_playfabid, plyr_playfabid, duration, reason) = res
			name_guess = guess_name(data, plyr_playfabid)
			#resolve discordid from playfabid
			adm_discordid = db.get_discordid_from_playfabid(adm_playfabid)
			adm_mention = ""
			adm_mention = adm_discordid and f"<@{adm_discordid}>"
			logmsg = "Logging ban: [{}] {} {} ({}) banned player {} ({}) for {}m (Reason: {}) ".format(timestamp, adm_mention, adm_name, adm_playfabid, name_guess, plyr_playfabid, duration, reason)
			printing and print(logmsg)
			callback and await callback(logmsg, "ban")
			continue
		if match := match_kick(line):
			res = format_kick(match)
			(timestamp, adm_name, adm_playfabid, plyr_playfabid, reason) = res
			name_guess = guess_name(data, plyr_playfabid)
			adm_discordid = db.get_discordid_from_playfabid(adm_playfabid)
			adm_mention = ""
			adm_mention = adm_discordid and f"<@{adm_discordid}>"
			logmsg = "Logging kick: [{}] {} {} ({}) kicked player {} ({}) (Reason: {})".format(timestamp, adm_mention, adm_name, adm_playfabid, name_guess, plyr_playfabid, reason)
			printing and print(logmsg)
			callback and await callback(logmsg, "kick")
			continue
		if match := match_unban(line):
			res = format_unban(match)
			(timestamp, adm_name, adm_playfabid, plyr_playfabid) = res
			name_guess = guess_name(data, plyr_playfabid)
			adm_discordid = db.get_discordid_from_playfabid(adm_playfabid)
			adm_mention = ""
			adm_mention = adm_discordid and f"<@{adm_discordid}>"
			logmsg = "Logging unban: [{}] {} {} ({}) unbanned player {} ({})".format(timestamp, adm_mention, adm_name, adm_playfabid, name_guess, plyr_playfabid)
			printing and print(logmsg)
			callback and await callback(logmsg, "unban")
			continue
		if match := match_update(line):
			logmsg = ""
			callback and await callback(logmsg, "update", match)
			continue

async def main():
	import mydb
	mydb = mydb.db()
	data = ""
	with open("test/test.log", "r") as fp:
		data = fp.read()
	await parse_lines(data, mydb)
	print(timestamp_to_datetime("2021.01.09-22.17.01:079"))

if __name__ == '__main__':
	import asyncio
	asyncio.run(main())
