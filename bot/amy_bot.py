from discord.ext import commands
from utils.help_command_utils import PartialHelp
from utils.cog_utils import PartialCommand
from utils.error_utils import ErrorHandler

# @TODO: logging
class AmyBot(commands.Bot, ErrorHandler):
	def __init__(self, prefix, *args, **kwargs):
		super().__init__(command_prefix=prefix, *args, **kwargs)
		self.help_command= PartialHelp()

		# hotfix to limit to hv_server members, will remove later
		for x in get_hv_checks(self): self.add_check(x)

	async def on_ready(self):
		print('Logged in as', self.user.name, self.user.id)
		# act = discord.Activity(name=f"{self.prefix}help for commands", type=discord.ActivityType.playing)
		# await self.change_presence(activity=act)


	# @ TODO: partial matching for aliases?
	# Override process_commands to allow for partial command name matching
	async def process_commands(self, message): # @todo: comment
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
		return await ErrorHandler.on_command_error(self, ctx, e)




#@todo: will remove later
# hotfix to limit to hv_server members because this will share a discord key with other bot
def get_hv_checks(client):
	test_id= 395741640372912138
	hv_id= 603053441157169155

	def check_hv_server(ctx):
		return ctx.guild is None or ctx.guild.id in [hv_id, test_id]

	async def check_hv_member(ctx):
		hv_server= client.get_guild(hv_id)
		for x in hv_server.members:
			if x.id == ctx.author.id:
				return True
		return False

	return [check_hv_server, check_hv_member]