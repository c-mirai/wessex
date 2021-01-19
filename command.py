from discord.ext import commands
import discordio

class Status(commands.Cog):
	def __init__(self, bot, ss):
		self.bot = bot
		self.status = ss

	@commands.command()
	async def status(self, ctx):
		await ctx.send(self.status.status())

	@commands.command()
	async def playerlist(self, ctx):
		pl = self.status.playerlist()
		if pl:
			await ctx.send(pl)
		else:
			await ctx.send("No players currently playing.")

def main():
	bot = commands.Bot(command_prefix='$')

	# @commands.command()
	# async def test(ctx, arg):
	# 	await ctx.send(arg)

	bot.add_cog(Status(bot))
	bot.run(discordio.TOKEN)

if __name__ == '__main__':
	main()