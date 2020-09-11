from discord.ext import commands
from utils.help_command_utils import PartialHelp
from utils.cog_utils import PartialCommand
from utils.error_utils import ErrorHandler
from utils.perm_utils import check_perms
from cogs import UpdateCog, AuctionCog, ItemCog


# @TODO: logging
class AmyBot(commands.Bot, ErrorHandler):
	def __init__(self, prefix, *args, **kwargs):
		super().__init__(command_prefix=prefix, *args, **kwargs)
		self.help_command= PartialHelp()


		# load cogs and checks
		self.add_cog(AuctionCog())
		self.add_cog(UpdateCog())
		self.add_cog(ItemCog())
		self.add_check(check_perms)



	# @ TODO: partial matching for aliases?
	# Override process_commands to allow for partial command name matching
	async def process_commands(self, message): # @todo: comment
		if message.author.bot:
			return

		# check for partial names
		ctx= await self.get_context(message)
		if ctx.invoked_with and ctx.command is None:
			for cmd in self.all_commands:
				if type(self.all_commands[cmd]) is PartialCommand and ctx.invoked_with.startswith(self.all_commands[cmd].short):
					ctx.command= self.all_commands[cmd]
					break

		# get query (eg !auction blah --> blah)
		ctx.query= message.content.split(maxsplit=1)
		ctx.query= ctx.query[1].strip() if len(ctx.query) > 1 else ""

		# start command and send "typing..." message
		if ctx.command is not None:
			# async with ctx.typing():
				await self.invoke(ctx)


	# handle errors during command
	async def on_command_error(self, ctx, e):
		return await ErrorHandler.on_command_error(self, ctx, e)
