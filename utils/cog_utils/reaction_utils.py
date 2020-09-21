from discord.ext import commands
from classes.errors import PermissionError, TemplatedError
from utils.perm_utils import check_perms
import utils, re, discord


# ---- Decorators for on_raw_reaction_add ----

# check for admin or server owner
def is_admin_owner(bot, payload):
	global_admins= utils.load_yaml(utils.GLOBAL_PERMS_FILE)['admins']
	user= bot.get_user(payload.user_id)

	is_dm= payload.guild_id is not None
	is_admin= global_admins and any(payload.user_id == global_admins[x] for x in global_admins)

	if is_dm or is_admin:
		pass
	else:
		guild= bot.get_guild(payload.guild_id)
		if user.id == guild.owner.id:
			pass
		else:
			return False

	return True


# check that message is not from self
def is_self(func):
	async def decorator(self, payload):
		channel= self.bot.get_channel(payload.channel_id)
		message= await channel.fetch_message(payload.message_id)

		if not message.author == self.bot.user:
			return

		await func(self, payload)

	return decorator

# check command permissions
async def _has_perms(command_name, self, payload):
	channel= self.bot.get_channel(payload.channel_id)
	message= await channel.fetch_message(payload.message_id)

	ctx= await self.bot.get_context(message)
	ctx.__dict__['cog']= self

	return check_perms(ctx=ctx, command_name=command_name)


# decorator for is_admin_owner, is_self, has_perms
def has_reaction_perms(command_name):
	def outer(func):
		async def inner(self, payload):
			# inits
			perm_check= await _has_perms(self=self, payload=payload, command_name=command_name)
			admin_check= is_admin_owner(bot=self.bot, payload=payload)

			# checks
			if not perm_check and not admin_check:
				return

			# passed checks
			await func(self, payload)

		return inner
	return outer


# ---- Converters and the like ----

RR_MESSAGE= "message"
RR_ROLE= "roles"
RR_EMOTE= "emotes"

# Enforce argument to rr commands are either "message", "roles", or "emotes"
def get_rr_type(string):
		sw= lambda x: string.lower().startswith(x.lower())

		if sw("msg") or sw("message"):
			return RR_MESSAGE
		elif sw("role"):
			return RR_ROLE
		elif sw("emote") or sw("emoji"):
			return RR_EMOTE
		else:
			raise TemplatedError("bad_rr_type", value=string)


# get users from string, case insensitive
async def parse_roles(string, ctx, bot):
	# inits
	ret= []
	guild_roles= await ctx.guild.fetch_roles()
	to_search= string

	# get exact id matches
	r_ids= re.findall(r"<@&(\d+)>", to_search)
	for x in r_ids:
		role= bot.get_role(int(x))
		to_search= to_search.replace(f"<@&{x}>", "")
		if role:
			ret.append(role)

	# get exact name matches
	for role in guild_roles:
		m= re.search(rf"\b{role.name}\b", to_search, flags=re.IGNORECASE)
		if m:
			ret.append(role)
			to_search= re.sub(rf"\b{role.name}\b", "", to_search, count=1, flags=re.IGNORECASE)

	# get partial name matches
	for role in guild_roles:
		m= re.search(rf"{role.name}", to_search, flags=re.IGNORECASE)
		if m:
			ret.append(role)
			to_search= re.sub(rf"{role.name}", "", to_search, count=1, flags=re.IGNORECASE)

	return dict(matches=ret, remainder=to_search)


# get emotes from string, case insensitive
async def parse_emotes(string, ctx, bot):
	ret= []
	emotes= bot.emojis
	spl= string.split()

	# get exact matches
	for i,x in enumerate(spl):
		ms= re.findall(r"<a?:[a-zA-Z0-9\_]+:([0-9]+)>", x, )

