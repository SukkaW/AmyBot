from discord.ext import commands

# todo: reference to bot
# todo: load cog config
class PartialCog(commands.Cog):
	def __init__(self, hidden=False, **kwargs):
		self.hidden=hidden
		super().__init__(**kwargs)