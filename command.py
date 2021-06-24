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

from discord.ext import commands
import discordio
import discord

class Status(commands.Cog):
	depmsg = "Command deprecated - check the <#801132836777099294> channel!"
	def __init__(self, bot, ss):
		self.bot = bot
		self.status = ss
	@commands.command()
	async def status(self, ctx):
		#await ctx.send(self.status.status())
		await ctx.send(self.depmsg)

	@commands.command()
	async def playerlist(self, ctx):
		pl = self.status.playerlist()
		# if pl:
		# 	await ctx.send(pl)
		# else:
		# 	await ctx.send("No players currently playing.")
		await ctx.send(self.depmsg)

async def is_admin(ctx):
	return bool(discord.utils.find(lambda r: r.permissions.administrator, ctx.author.roles))

class DB(commands.Cog):
	def __init__(self, bot, db):
		self.bot = bot
		self.db = db
		self.q_get_all_bans = "SELECT * FROM bans"
		self.q_get_all_players = "SELECT * FROM players"

	@commands.group()
	@commands.check(is_admin)
	async def bans(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Invalid bans command.")

	@bans.command()
	async def all(self, ctx):
		"""Gets a list of all ban information in the system."""
		paginator = commands.Paginator()
		res = await self.db.fetch_all(self.q_get_all_bans)
		for line in res:
			paginator.add_line(str(line))
		for page in paginator.pages:
			await ctx.send(page)

	@bans.command()
	async def admin(self, ctx, id):
		"""Gets a list of all ban information in the system."""
		q = f"SELECT * FROM bans WHERE AdminID='{id}'"
		paginator = commands.Paginator()
		res = await self.db.fetch_all(q)
		if not len(res):
			await ctx.send("No bans found by that admin.")
		for line in res:
			paginator.add_line(str(line))
		for page in paginator.pages:
			await ctx.send(page)

	@bans.command()
	async def player(self, ctx, id):
		"""Gets a list of all ban information in the system."""
		q = f"SELECT * FROM bans WHERE PlayerID='{id}'"
		paginator = commands.Paginator()
		res = await self.db.fetch_all(q)
		if not len(res):
			await ctx.send("No bans found for that player.")
		for line in res:
			paginator.add_line(str(line))
		for page in paginator.pages:
			await ctx.send(page)

	@commands.group()
	@commands.check(is_admin)
	async def players(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Invalid players command.")

	@players.command()
	async def all(self, ctx):
		"""Gets a list of all ban information in the system."""
		paginator = commands.Paginator()
		res = await self.db.fetch_all(self.q_get_all_players)
		for line in res:
			paginator.add_line(str(line))
		for page in paginator.pages:
			await ctx.send(page)

def main():
	bot = commands.Bot(command_prefix='$')

	# @commands.command()
	# async def test(ctx, arg):
	# 	await ctx.send(arg)

	bot.add_cog(Status(bot))
	bot.run(discordio.TOKEN)

if __name__ == '__main__':
	main()