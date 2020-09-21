from classes import PartialCog, PartialCommand
from utils.cog_utils.reaction_utils import has_reaction_perms, is_self
from utils.cog_utils import reaction_utils as React
from discord.ext import commands
import utils, discord


"""
For various reaction-related functions.
"""
class ReactionCog(PartialCog, name="Reaction"):
	def __init__(self, bot, **kwargs):
		super().__init__(**kwargs)
		self.hidden=False
		self.bot= bot


	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		for x in [self.reaction_delete]:
			await x(payload)


	@commands.command(name="addrr", short="addrr", cls=PartialCommand)
	async def addrr(self, ctx):
		print(ctx.query)

	# delete bot messages reacted to with CONFIG['deletion_emote']
	@is_self
	@has_reaction_perms(command_name="reaction_delete")
	async def reaction_delete(self, payload):
		# inits
		CONFIG= utils.load_yaml(utils.REACTION_CONFIG)
		channel= self.bot.get_channel(payload.channel_id)
		message= await channel.fetch_message(payload.message_id)

		# check emoji
		if payload.emoji.is_unicode_emoji() and str(payload.emoji) == CONFIG['deletion_emote']:
			await message.delete()