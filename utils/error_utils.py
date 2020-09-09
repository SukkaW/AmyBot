from discord.ext import commands
from utils.perm_utils import PermissionFailure
from utils.parse_utils import ParseError
import utils, traceback, sys

# mixin for globally handling errors
class ErrorHandler:
	async def on_command_error(self, ctx, e):
		if isinstance(e, PermissionFailure):
			return await ctx.send(e.render())
		elif isinstance(e, ParseError):
			return await ctx.send(e.render(ctx))
		# @TODO: generic error
		else:
			return await self.handle_other_error(ctx, e)

	# Unexpected errors
	async def handle_other_error(self, ctx, e):
		# get the actual stack trace if available
		if isinstance(e, commands.CommandInvokeError):
			err= e.original
		else: err= e

		# dump into template
		ERROR_STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)
		text= "\n".join(traceback.format_tb(err.__traceback__)) + "\n" + str(e)
		uncaught= utils.render(ERROR_STRINGS['uncaught_template'], dict(EXCEPTION=text[-1400:], MESSAGE=ctx.message.content[:400]))

		# print
		await ctx.send(uncaught)
		traceback.print_tb(err.__traceback__)
		sys.stderr.write(str(e))

# error whose render() method automatically selects an appropriate template based on name
class GenericError:
	def __init__(self, error_name, **kwargs):
		self.error_name= error_name
		self.kwargs= kwargs

	def render(self, ctx):
		ERROR_STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)

		name= self.error_name.replace("_template", "")
		template_name= f"{self.error_name}_template"

		if template_name not in ERROR_STRINGS:
			available= [x for x in ERROR_STRINGS if x.endswith("template")]
			return utils.render(ERROR_STRINGS['tmp_not_found_template'], dict(NAME=name, AVAILABLE=available))

		await ctx.send(utils.render(ERROR_STRINGS[template_name], self.kwargs))