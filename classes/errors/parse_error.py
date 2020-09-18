from discord.ext.commands.errors import CommandError
import utils

class ParseError(CommandError):
	def __init__(self, keyword=None, value=None, exception=None):
		"""
		Error when parsing a string value.
		:param keyword: Keyword that the value belongs to
		:param value: String being parsed
		:param func: Parsing function
		"""

		self.keyword= keyword
		self.value= value
		self.exception= exception

	def render(self, ctx):
		COG_STRINGS= utils.load_yaml(utils.COG_STRING_FILE)
		ERROR_STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)

		reps= {
			"PREFIX": ctx.prefix,
			"COMMAND": ctx.command.name,
			"ARGS": COG_STRINGS[ctx.command.cog.qualified_name]['commands'][ctx.command.name]['args'],
			"VALUE": self.value,
			"KEYWORD": self.keyword,
			"EXCEPTION": str(self.exception)
		}

		return utils.render(ERROR_STRINGS['usage_template'], reps)

	def __str__(self):
		STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)
		reps= {
			"VALUE": self.value,
			"KEYWORD": self.keyword,
			"EXCEPTION": str(self.exception)
		}
		return utils.render(STRINGS['parse_console_template'], reps)