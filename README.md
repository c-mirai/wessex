# wessex
**A log-reading bot for mordhau.**

For servers that don't have RCON support (like gportal), this bot can read the logs via FTP and pull relevant info into discord.

## Features

### Server status

Track who is in the server, player count, map, and other server info.

<img src="serverstatus.png" alt="Server Status" /> 

### Administrative tracking

Detect bans, unbans, kicks, mutes, unmutes.

<img src="bans.png" alt="bans" />

### Chat tracking with batching

Easily keep up with chat thanks to batching chat messages.

<img src="chats.png" alt="chats" />

*A single batched chat message.*

## Setup
Rename `config.ini.template` to `config.ini` and `admins.json.template` to `admins.json`.

Fill in the blank fields in `config.ini`.

`guilds` should be an array of server names in JSON format, example:

```
[discord.guilds]
guilds=["myserver","myotherserver"]
```

Most of the other settings don't need to be changed. `throttle` is the download speed in bytes, 20 KB/s by default. Keep this low to make sure pings won't be affected in your server.