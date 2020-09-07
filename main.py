from discord.ext import commands
from utils.help_utils import PartialHelp
from utils.cog_utils import PartialCommand
import utils, json, cogs, yaml

BOT_CONFIG= json.load(open(utils.BOT_CONFIG_FILE))

class AmyBot(commands.Bot):
	def __init__(self, prefix, *args, **kwargs):
		super().__init__(command_prefix=prefix, *args, **kwargs)
		self.help_command= PartialHelp()

	async def on_ready(self):
		print('Logged in as', self.user.name, self.user.id)
		# act = discord.Activity(name=f"{self.prefix}help for commands", type=discord.ActivityType.playing)
		# await self.change_presence(activity=act)

	# @ TODO: partial matching for aliases?
	# Override process_commands to allow for partial command name matching
	async def process_commands(self, message):
		if message.author.bot:
			return

		ctx= await self.get_context(message)
		if ctx.invoked_with and ctx.command is None:
			for cmd in self.all_commands:
				if type(self.all_commands[cmd]) is PartialCommand and ctx.invoked_with.startswith(self.all_commands[cmd].short):
					ctx.command= self.all_commands[cmd]
					break

		ctx.query= message.content.split(maxsplit=1)
		ctx.query= ctx.query[1].strip() if len(ctx.query) > 1 else ""

		if ctx.command is not None:
			await self.invoke(ctx)

	async def on_command_error(self, ctx, e):
		import traceback, sys

		if isinstance(e, commands.CommandInvokeError):
			err= e.original
		else: err= e

		ERROR_STRINGS= yaml.safe_load(open(utils.ERROR_STRING_FILE))

		text= "\n".join(traceback.format_tb(err.__traceback__)) + "\n" + str(e)
		uncaught= utils.render(ERROR_STRINGS['uncaught_template'], dict(EXCEPTION=text[-1400:], MESSAGE=ctx.message.content[:400]))
		await ctx.send(uncaught)

		traceback.print_tb(err.__traceback__)
		sys.stderr.write(str(e))

bot= AmyBot(BOT_CONFIG['prefix'], case_insensitive=True)
bot.add_cog(cogs.AuctionCog())
bot.run(BOT_CONFIG['discord_key'])