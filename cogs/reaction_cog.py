from classes import PartialCog, PartialCommand
from utils.cog_utils.reaction_utils import has_reaction_perms, is_self
from utils.cog_utils import reaction_utils as React
from discord.ext import commands
from ruamel import yaml
import utils, discord, json


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
		# inits
		message_dict= React.parse_message_json(ctx.query)
		msg= await ctx.send(content=message_dict['content'],
							embed=discord.Embed.from_dict(message_dict['embed']))

		# edit log
		React.edit_rr_log(msg, message_dict=message_dict)
		return

	@commands.command(name="editrr", short="editrr", cls=PartialCommand)
	async def editrr(self, ctx):
		msg, query= await React.get_rr_message(ctx.query, ctx, self.bot)
		typ, query= React.get_rr_type(query, ctx)

		# if edit msg
		if typ == React.RR_MESSAGE:
			# inits
			message_dict= React.parse_message_json(query)
			await msg.edit(content=message_dict['content'],
						   embed=discord.Embed.from_dict(message_dict['embed']))

			# edit log
			React.edit_rr_log(msg, message_dict=message_dict)
			return


		# if edit roles
		elif typ == React.RR_ROLE:
			# edit log
			roles, remainder= React.parse_roles(query, ctx, self.bot)
			entry= React.edit_rr_log(msg, roles=roles)

			# notify user
			emotes= React.get_emotes(entry['emotes'], bot=self.bot, ctx=ctx, message=msg)
			await React.notify_rr_emote_role_edit(ctx, roles, emotes, remainder, message=msg)
			return


		# if edit emotes
		elif typ == React.RR_EMOTE:
			# edit log
			emotes, remainder= React.parse_emotes(query, ctx, self.bot)
			entry= React.edit_rr_log(msg, emotes=emotes)

			# edit msg
			await msg.clear_reactions()
			for x in emotes:
				await msg.add_reaction(x)

			# notify user
			roles= React.get_roles(entry['roles'], bot=self.bot, ctx=ctx, message=msg)
			await React.notify_rr_emote_role_edit(ctx, roles, emotes, remainder, message=msg)
			return

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