import re
import mydb
from namecache import Namecache

db = mydb.db()
name_cache = Namecache()

def parser(Parser):
	"""Class decorator. Adds an instance of Parser to the list of parsers."""
	Parser.parsers.append(Parser())
	return Parser

class Parser:
	parsers = []

	async def parse(self, line):
		match = self.match(line)
		# print(f"Match: {match}")
		if not match: return False

		data = self.format(match)

		return await self.handle(data)
	
	def match(self, line):
		# print(f'Matching {line} to {self.pattern}')
		return self.pattern.match(line)
	
	def format(self, match):
		pass
	
	async def handle(data):
		pass

@parser
class BanParser(Parser):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) banned player (.*) \(Duration: (\d*), Reason: (.*)\)\r\n")
	
	def format(self, match):
		data = {
			"timestamp"	 		: match.group(1),
			"adm_name" 			: match.group(2),
			"adm_playfabid" 	: match.group(3),
			"plyr_playfabid" 	: match.group(4),
			"duration" 			: match.group(5),
			"reason"			: match.group(6),
		}
		return data
	
	async def handle(self, data):
		name_guess = guess_name(data['plyr_playfabid'])
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
		return {
			'message': logmsg,
			'type': 'ban',
			'data': data,
		}

@parser
class KickParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) kicked player (.*) \(Reason: (.*)\)\r\n")
    
    def format(self, match):
        data = {
            "timestamp"	 		: match.group(1),
            "adm_name" 			: match.group(2),
            "adm_playfabid" 	: match.group(3),
            "plyr_playfabid" 	: match.group(4),
            "reason"			: match.group(5),
        }
        return data

    async def handle(self, data):
        name_guess = guess_name(data['plyr_playfabid'])
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
        return {
            'message': logmsg,
            'type': 'kick',
            'data': data
        }

@parser
class UnbanParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) unbanned player (.*)\r\n")
    
    def format(self, match):
        data = {
            "timestamp"	 		: match.group(1),
            "adm_name" 			: match.group(2),
            "adm_playfabid" 	: match.group(3),
            "plyr_playfabid" 	: match.group(4),
        }
        return data

    async def handle(self, data):
        name_guess = guess_name(data['plyr_playfabid'])
        adm_discordid = await db.get_discordid_from_playfabid(data['adm_playfabid'])
        adm_mention = adm_discordid and f"<@{adm_discordid}>" or ''
        logmsg = "[{}] {} {} ({}) unbanned {} ({})".format(
            data['timestamp'],
            adm_mention,
            data['adm_name'],
            data['adm_playfabid'],
            name_guess,
            data['plyr_playfabid'])
        return {
            'message': logmsg,
            'type': 'unban',
            'data': data
        }

@parser
class ChatParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogGameMode: Display: \((.*)\) (.*), (.*): \"(.*)\"\r\n")
    
    def format(self, match):
        data = {
            "timestamp"	 		: match.group(1),
            "mode" 				: match.group(2),
            "name" 				: match.group(3),
            "plyr_playfabid"	: match.group(4),
            "msg" 				: match.group(5),
        }
        return data

    async def handle(self, data):
        logmsg = "[{}] ({}) {} ({}): {}".format(
            data['timestamp'],
            data['plyr_playfabid'],
            data['name'], 
            data['mode'],
            data['msg'])
        return {
            'message': logmsg,
            'type': 'chat',
            'data': data
        }

@parser
class UpdateParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogPlayFabAPI: Verbose: UpdateGameServer \(Map: (.*), GameMode: (.*), Players: (.*), ReservedSlots: (.*)\)\r\n")
    
    def format(self, match):
        data = {
            "timestamp" 		: match.group(1),
            "mapname"			: match.group(2),
            "mode" 				: match.group(3),
            "playernum" 		: match.group(4),
            "reservedslots" 	: match.group(5),
        }
        return data

    async def handle(self, data):
        logmsg = ""
        return {
            'message': logmsg,
            'type': 'update',
            'data': data
        }

@parser
class PlyrjoinParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauGameSession: PlayFab authentication for (.*) \((.*)\) completed successfully\r\n")
    
    def format(self, match):
        data = {
            "timestamp" 		: match.group(1),
            "plyr_name" 		: match.group(2),
            "plyr_playfabid"	: match.group(3),
        }
        return data

    async def handle(self, data):
        logmsg = ""
        return {
            'message': logmsg,
            'type': 'plyrjoin',
            'data': data
        }

@parser
class AdmjoinParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauGameSession: Player (.*) \((.*)\) is an admin\r\n")
    
    def format(self, match):
        data = {
            "timestamp" 		: match.group(1),
            "plyr_name" 		: match.group(2),
            "plyr_playfabid"	: match.group(3),
        }
        return data

    async def handle(self, data):
        logmsg = ""
        return {
            'message': logmsg,
            'type': 'admjoin',
            'data': data
        }

@parser
class PlyrleaveParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogNet: UChannel::Close: Sending CloseBunch. .*\[UNetConnection] RemoteAddr: (.*?),.* UniqueId: MordhauOnlineSubsystem:(.*)\r\n")
    
    def format(self, match):
        data = {
            "timestamp" 		: match.group(1),
            "plyr_addr" 		: match.group(2),
            "plyr_playfabid"	: match.group(3)
        }
        return data

    async def handle(self, data):
        logmsg = ""
        return {
            'message': logmsg,
            'type': 'plyrleave',
            'data': data
        }

@parser
class RegisterParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogPlayFabAPI: Verbose: RegisterGameServer \(Version: (.*), ServerName: (.*), Map: (.*), GameMode: (.*), Players: (.*), MaxPlayers: (.*), ReservedSlots: (.*), Region: (.*), IP: (.*), GamePort: (.*), BeaconPort: (.*), bAllowJoin: (.*), bIsPasswordProtected: (.*), Mods: (.*), OperatingSystem: (.*)\)\r\n")
    
    def format(self, match):
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

    async def handle(self, data):
        logmsg = ""
        return {
            'message': logmsg,
            'type': 'register',
            'data': data
        }

@parser
class MuteParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) muted player (.*) \(Duration: (.*)\)\r\n")
    
    def format(self, match):
        data = {
            "timestamp"		: match.group(1),
            "adm_name"		: match.group(2),
            "adm_playfabid"	: match.group(3),
            "plyr_playfabid": match.group(4),
            "duration"		: match.group(5),
        }
        return data

    async def handle(self, data):
        name_guess = guess_name(res["plyr_playfabid"])
        adm_discordid = await db.get_discordid_from_playfabid(res["adm_playfabid"])
        adm_mention = adm_discordid and f"<@{adm_discordid}>" or ''
        logmsg = (f"[{res['timestamp']}]"
                    f"{adm_mention} {res['adm_name']} ({res['adm_playfabid']})"
                    f"muted {name_guess} ({res['plyr_playfabid']})"
                    f"(Duration: {res['duration']})")
        return {
            'message': logmsg,
            'type': 'mute',
            'data': data
        }

@parser
class UnmuteParser(Parser):
    def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
        self.pattern = re.compile(r"\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]\[.{0,4}\]LogMordhauPlayerController: Display: Admin (.*) \((.*)\) unmuted player (.*)\r\n")
    
    def format(self, match):
        data = {
            "timestamp"		: match.group(1),
            "adm_name"		: match.group(2),
            "adm_playfabid"	: match.group(3),
            "plyr_playfabid": match.group(4),
        }
        return data

    async def handle(self, data):
        name_guess = guess_name(res["plyr_playfabid"])
        adm_discordid = await db.get_discordid_from_playfabid(res["adm_playfabid"])
        adm_mention = adm_discordid and f"<@{adm_discordid}>" or ''
        logmsg = (f"[{res['timestamp']}] {adm_mention} {res['adm_name']}"
                    f"({res['adm_playfabid']}) unmuted"
                    f"{name_guess} ({res['plyr_playfabid']})")
        return {
            'message': logmsg,
            'type': 'mute',
            'data': data
        }