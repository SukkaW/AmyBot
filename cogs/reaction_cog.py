from classes import PartialCog, PartialCommand
from utils.cog_utils.reaction_utils import check_admin_owner, check_self
from discord.ext import commands
import utils


"""
For various reaction-related functions.
"""
class ReactionCog(PartialCog, name="Reaction"):
	def __init__(self, bot, **kwargs):
		super().__init__(**kwargs)
		self.hidden=True
		self.bot= bot

		self.hv_role_msg= None
		self.hv_role_ch= None


	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		for x in [self.poop_delete]:
			await x(payload)


	async def hv_reaction_roles(self, payload):
		# get channel
		if self.hv_role_ch is None:
			CONFIG= utils.load_yaml(utils.BOT_CONFIG_FILE)
			self.hv_role_ch= self.bot.get_channel(CONFIG['reaction_role_channel'])


	async def get_hv_reaction_msg(self, channel):
		# get last message in channel
		if self.hv_role_msg is None:
			async for msg in self.hv_role_ch.history(limit=1):
				last_msg= msg

			# if non-bot messsage, post new one



	# delete bot messages reacted to with 💩
	@check_self
	@check_admin_owner
	async def poop_delete(self, payload):
		# inits
		channel= self.bot.get_channel(payload.channel_id)
		message= await channel.fetch_message(payload.message_id)

		# check emoji
		if payload.emoji.is_unicode_emoji() and str(payload.emoji) == "💩":
			await message.delete()
		else:
			print(payload.emoji)