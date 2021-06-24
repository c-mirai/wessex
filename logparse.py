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

import re
import io
import datetime
#from db import db

timestamp_pattern 	= re.compile(r"\[\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3}\]")
microsecond_pattern = re.compile(r":(\d{3})\]")
ban_pattern 		= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) banned player (.*) \(Duration: (\d*), Reason: (.*)\)\r\n")
kick_pattern 		= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) kicked player (.*) \(Reason: (.*)\)\r\n")
kickban_pattern 	= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauGameSession: Kicked player (.*) \((.*)\), reason: (.*)\r\n")
unban_pattern 		= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) unbanned player (.*)\r\n")
chat_pattern 		= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogGameMode: Display: \((.*)\) (.*), (.*): \"(.*)\"\r\n")
update_pattern 		= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogPlayFabAPI: Verbose: UpdateGameServer \(Map: (.*), GameMode: (.*), Players: (.*), ReservedSlots: (.*)\)\r\n")
plyrjoin_pattern 	= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauGameSession: PlayFab authentication for (.*) \((.*)\) completed successfully\r\n")
admjoin_pattern 	= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauGameSession: Player (.*) \((.*)\) is an admin\r\n")
#plyrleave_pattern 	= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauGameSession: Verbose: Freed slot occupied by player (.*) \((.*)\)\r\n")
plyrleave_pattern 	= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogNet: UChannel::Close: Sending CloseBunch. .*\[UNetConnection] RemoteAddr: (.*?),.* UniqueId: MordhauOnlineSubsystem:(.*)\r\n")
register_pattern 	= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogPlayFabAPI: Verbose: RegisterGameServer \(Version: (.*), ServerName: (.*), Map: (.*), GameMode: (.*), Players: (.*), MaxPlayers: (.*), ReservedSlots: (.*), Region: (.*), IP: (.*), GamePort: (.*), BeaconPort: (.*), bAllowJoin: (.*), bIsPasswordProtected: (.*), Mods: (.*), OperatingSystem: (.*)\)\r\n")
mute_pattern 		= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) muted player (.*) \(Duration: (.*)\)\r\n")
unmute_pattern		= re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) unmuted player (.*)\r\n")

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
	guessname_pattern = re.compile(r"(P|p)layer (.*) \({}\)".format(playfabid))
	match = guessname_pattern.search(data)
	if match:
		return match.group(2)
	return ""

def format_ban(match):
	data = {
		"timestamp"	 		: match.group(1),
		"adm_name" 			: match.group(2),
		"adm_playfabid" 	: match.group(3),
		"plyr_playfabid" 	: match.group(4),
		"duration" 			: match.group(5),
		"reason"			: match.group(6),
	}
	return data

def format_kick(match):
	data = {
		"timestamp"	 		: match.group(1),
		"adm_name" 			: match.group(2),
		"adm_playfabid" 	: match.group(3),
		"plyr_playfabid" 	: match.group(4),
		"reason"			: match.group(5),
	}
	return data

def format_unban(match):
	data = {
		"timestamp"	 		: match.group(1),
		"adm_name" 			: match.group(2),
		"adm_playfabid" 	: match.group(3),
		"plyr_playfabid" 	: match.group(4),
	}
	return data

def format_chat(match):
	data = {
		"timestamp"	 		: match.group(1),
		"mode" 				: match.group(2),
		"name" 				: match.group(3),
		"plyr_playfabid"	: match.group(4),
		"msg" 				: match.group(5),
	}
	return data

def format_update(match):
	data = {
		"timestamp" 		: match.group(1),
		"mapname"			: match.group(2),
		"mode" 				: match.group(3),
		"playernum" 		: match.group(4),
		"reservedslots" 	: match.group(5),
	}
	return data

def format_plyrjoin(match):
	data = {
		"timestamp" 		: match.group(1),
		"plyr_name" 		: match.group(2),
		"plyr_playfabid"	: match.group(3),
	}
	return data

def format_admjoin(match):
	data = {
		"timestamp" 		: match.group(1),
		"plyr_name" 		: match.group(2),
		"plyr_playfabid"	: match.group(3),
	}
	return data

def format_plyrleave(match):
	data = {
		"timestamp" 		: match.group(1),
		"plyr_addr" 		: match.group(2),
		"plyr_playfabid"	: match.group(3)
	}
	return data

def format_register(match):
	data = {
		"timestamp" 	: match.group(1),
		"version"		: match.group(2),
		"server_name"	: match.group(3),
		"map_name"		: match.group(4),
		"gamemode"		: match.group(5),
		"players"		: match.group(6),
		"max_players"	: match.group(7),
		"reserved_slots": match.group(8),
		"region"		: match.group(9),
		"ip"			: match.group(10),
		"game_port"		: match.group(11),
		"beacon_port"	: match.group(12),
		"allow_join"	: match.group(13),
		"is_pw"			: match.group(14),
		"mods"			: match.group(15),
		"os"			: match.group(16),
	}
	return data

def format_mute(match):
	data = {
		"timestamp"		: match.group(1),
		"adm_name"		: match.group(2),
		"adm_playfabid"	: match.group(3),
		"plyr_playfabid": match.group(4),
		"duration"		: match.group(5),
	}
	return data

def format_unmute(match):
	data = {
		"timestamp"		: match.group(1),
		"adm_name"		: match.group(2),
		"adm_playfabid"	: match.group(3),
		"plyr_playfabid": match.group(4),
	}
	return data



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

def match_plyrjoin(line):
	return plyrjoin_pattern.match(line)

def match_admjoin(line):
	return admjoin_pattern.match(line)

def match_plyrleave(line):
	return plyrleave_pattern.match(line)

def match_mute(line):
	return mute_pattern.match(line)

def match_unmute(line):
	return unmute_pattern.match(line)

patterns = ['ban', 'kick', 'unban', 'chat', 'update', 'plyrjoin', 'admjoin',
			'plyrleave', 'mute', 'unmute']
async def handle_chat(data, full_log, msg_handler):
	logmsg = "[{}] ({}) {} ({}): {}".format(
		data['timestamp'],
		data['plyr_playfabid'],
		data['name'],
		data['mode'],
		data['msg'])
	msg_handler and await msg_handler(logmsg, "chat", data)

async def handle_ban(data, full_log, msg_handler):
	name_guess = guess_name(full_log, data['plyr_playfabid'])
	#resolve discordid from playfabid
	adm_discordid = await db.get_discordid_from_playfabid(data['adm_playfabid'])
	adm_mention = adm_discordid and f'<@{adm_discordid}>' or ''
	logmsg = "[{}] {} {} ({}) banned {} ({}) (Length: {}, Reason: {}) ".format(
		data['timestamp'],
		adm_mention,
		data['adm_name'],
		data['adm_playfabid'],
		name_guess,
		data['plyr_playfabid'],
		data['duration'],
		data['reason'])
	msg_handler and await msg_handler(logmsg, "ban", data)

async def handle_kick(data, full_log, msg_handler):
	name_guess = guess_name(full_log, data['plyr_playfabid'])
	adm_discordid = await db.get_discordid_from_playfabid(data['adm_playfabid'])
	adm_mention = adm_discordid and f"<@{adm_discordid}>" or ''
	logmsg = "[{}] {} {} ({}) kicked {} ({}) (Reason: {})".format(
		data['timestamp'],
		adm_mention,
		data['adm_name'],
		data['adm_playfabid'],
		name_guess,
		data['plyr_playfabid'],
		data['reason'])
	msg_handler and await msg_handler(logmsg, "kick", data)

async def handle_unban(data, full_log, msg_handler):
	name_guess = guess_name(full_log, data['plyr_playfabid'])
	adm_discordid = await db.get_discordid_from_playfabid(data['adm_playfabid'])
	adm_mention = adm_discordid and f"<@{adm_discordid}>" or ''
	logmsg = "[{}] {} {} ({}) unbanned {} ({})".format(
		data['timestamp'],
		adm_mention,
		data['adm_name'],
		data['adm_playfabid'],
		name_guess,
		data['plyr_playfabid'])
	msg_handler and await msg_handler(logmsg, "unban", data)

async def handle_update(data, full_log, msg_handler):
	logmsg = ""
	msg_handler and await msg_handler(logmsg, "update", data)

async def handle_plyrjoin(data, full_log, msg_handler):
	logmsg = ""
	msg_handler and await msg_handler(logmsg, "plyrjoin", data)

async def handle_admjoin(data, full_log, msg_handler):
	logmsg = ""
	msg_handler and await msg_handler(logmsg, "admjoin", data)

async def handle_plyrleave(data, full_log, msg_handler):
	logmsg = ""
	msg_handler and await msg_handler(logmsg, "plyrleave", data)

async def handle_mute(data, full_log, msg_handler):
	name_guess = guess_name(full_log, res["plyr_playfabid"])
	adm_discordid = await db.get_discordid_from_playfabid(res["adm_playfabid"])
	adm_mention = adm_discordid and f"<@{adm_discordid}>" or ''
	logmsg = (f"[{res['timestamp']}]"
				f"{adm_mention} {res['adm_name']} ({res['adm_playfabid']})"
				f"muted {name_guess} ({res['plyr_playfabid']})"
				f"(Duration: {res['duration']})")
	msg_handler and await msg_handler(logmsg, "mute", data)

async def handle_unmute(data, full_log, msg_handler):
	name_guess = guess_name(full_log, res["plyr_playfabid"])
	adm_discordid = await db.get_discordid_from_playfabid(res["adm_playfabid"])
	adm_mention = adm_discordid and f"<@{adm_discordid}>" or ''
	logmsg = (f"[{res['timestamp']}] {adm_mention} {res['adm_name']}"
	 			f"({res['adm_playfabid']}) unmuted"
	 			f"{name_guess} ({res['plyr_playfabid']})")
	msg_handler and await msg_handler(logmsg, "mute", data)

async def handle_line(line, full_log, msg_handler):
	"""Determine the line type, format it, and call its handler function."""
	match = None
	msgtype = ''
	for pat in patterns:
		# check against every regex pattern
		match = globals()[f'{pat}_pattern'].match(line)
		if match:
			msgtype = pat
			break
	if not match or not msgtype: return
	# call the corosponding format function
	data = globals()[f'format_{msgtype}'](match)
	# call the corrosponding handler function
	await globals()[f'handle_{msgtype}'](data, full_log, msg_handler)

async def parse_lines_n(full_log, msg_handler=None):
	"""Loop through every line in full_log and call handle_line on it."""
	buf = io.StringIO(full_log)
	line = "True"
	while(line):
		line = buf.readline()
		await handle_line(line, full_log, msg_handler)

async def parse_lines(data, db, callback=None, printing=False):
	"""loops through every line in the log and determines its type, formats the log msg then calls callback on it

	data - the log data to loop over, string
	db - a mydb object to assist with playfabid->discordid resoltion
	callback - a function that gets called on each log message. takes two arguments, logmsg string and type string"""
	buf = io.StringIO(data)
	line = "True"
	match = None
	#printing = False
	while(line):
		line = buf.readline()
		match = match_chat(line)
		if match:
			res = format_chat(match)
			(timestamp, mode, name, plyr_playfabid, msg) = (res[k] for k in res) #requires python 3.7
			logmsg = "[{}] ({}) {} ({}): {}".format(timestamp, plyr_playfabid, name, mode, msg)
			printing and print(logmsg)
			callback and await callback(logmsg, "chat", match)
			continue
		match = match_ban(line)
		if match:
			res = format_ban(match)
			(timestamp, adm_name, adm_playfabid, plyr_playfabid, duration, reason) = (res[k] for k in res) #requires python 3.7
			name_guess = guess_name(data, plyr_playfabid)
			#resolve discordid from playfabid
			adm_discordid = await db.get_discordid_from_playfabid(adm_playfabid)
			adm_mention = ""
			adm_mention = adm_discordid and f"<@{adm_discordid}>"
			logmsg = "[{}] {} {} ({}) banned {} ({}) (Length: {}, Reason: {}) ".format(timestamp, adm_mention, adm_name, adm_playfabid, name_guess, plyr_playfabid, duration, reason)
			printing and print(logmsg)
			callback and await callback(logmsg, "ban", match)
			continue
		match = match_kick(line)
		if match:
			res = format_kick(match)
			(timestamp, adm_name, adm_playfabid, plyr_playfabid, reason) = (res[k] for k in res) #requires python 3.7
			name_guess = guess_name(data, plyr_playfabid)
			adm_discordid = await db.get_discordid_from_playfabid(adm_playfabid)
			adm_mention = ""
			adm_mention = adm_discordid and f"<@{adm_discordid}>"
			logmsg = "[{}] {} {} ({}) kicked {} ({}) (Reason: {})".format(timestamp, adm_mention, adm_name, adm_playfabid, name_guess, plyr_playfabid, reason)
			printing and print(logmsg)
			callback and await callback(logmsg, "kick", match)
			continue
		match = match_unban(line)
		if match:
			res = format_unban(match)
			(timestamp, adm_name, adm_playfabid, plyr_playfabid) = (res[k] for k in res) #requires python 3.7
			name_guess = guess_name(data, plyr_playfabid)
			adm_discordid = await db.get_discordid_from_playfabid(adm_playfabid)
			adm_mention = ""
			adm_mention = adm_discordid and f"<@{adm_discordid}>"
			logmsg = "[{}] {} {} ({}) unbanned {} ({})".format(timestamp, adm_mention, adm_name, adm_playfabid, name_guess, plyr_playfabid)
			printing and print(logmsg)
			callback and await callback(logmsg, "unban", match)
			continue
		match = match_update(line)
		if match:
			logmsg = ""
			callback and await callback(logmsg, "update", match)
			continue
		match = match_plyrjoin(line)
		if match:
			logmsg = ""
			callback and await callback(logmsg, "plyrjoin", match)
			continue
		match = match_admjoin(line)
		if match:
			logmsg = ""
			callback and await callback(logmsg, "admjoin", match)
			continue
		match = match_plyrleave(line)
		if match:
			logmsg = ""
			callback and await callback(logmsg, "plyrleave", match)
			continue
		match = match_mute(line)
		if match:
			res = format_mute(match)
			name_guess = guess_name(data, res["plyr_playfabid"])
			adm_discordid = await db.get_discordid_from_playfabid(res["adm_playfabid"])
			adm_mention = ""
			adm_mention = adm_discordid and f"<@{adm_discordid}>"
			logmsg = f"[{res['timestamp']}] {adm_mention} {res['adm_name']} ({res['adm_playfabid']}) muted {name_guess} ({res['plyr_playfabid']}) (Duration: {res['duration']})"
			printing and print(logmsg)
			callback and await callback(logmsg, "mute", match)
			continue
		match = match_unmute(line)
		if match:
			res = format_unmute(match)
			name_guess = guess_name(data, res["plyr_playfabid"])
			adm_discordid = await db.get_discordid_from_playfabid(res["adm_playfabid"])
			adm_mention = ""
			adm_mention = adm_discordid and f"<@{adm_discordid}>"
			logmsg = f"[{res['timestamp']}] {adm_mention} {res['adm_name']} ({res['adm_playfabid']}) unmuted {name_guess} ({res['plyr_playfabid']})"
			printing and print(logmsg)
			callback and await callback(logmsg, "mute", match)
			continue

async def main():
	import sqlitedb
	mydb = sqlitedb.db()
	data = ""
	with open("Mordhau.log", "rb") as fp:
		data = fp.read()
	await parse_lines(data.decode(), mydb, printing=True)
	print(timestamp_to_datetime("2021.01.09-22.17.01:079"))

if __name__ == '__main__':
	import asyncio
	asyncio.run(main())
