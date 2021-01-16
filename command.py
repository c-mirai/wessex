from discord.ext import commands
import discordio

class Status(commands.Cog):
	def __init__(self, bot, ss):
		self.bot = bot
		self.status = ss
		print(self.status)
		print("test")

	@commands.command()
	async def status(self, ctx):
		await ctx.send(self.status.str())

	async def playerlist(self, ctx):
		pass

def main():
	bot = commands.Bot(command_prefix='$')

	# @commands.command()
	# async def test(ctx, arg):
	# 	await ctx.send(arg)

	bot.add_cog(Status(bot))
	bot.run(discordio.TOKEN)

if __name__ == '__main__':
	main()