import utils


# decorators ---

def check_admin_owner(func):
	async def dec(self, payload):
		global_admins= utils.load_yaml(utils.GLOBAL_PERMS_FILE)['admins']
		user= self.bot.get_user(payload.user_id)

		# check for admin or server owner
		is_dm= payload.guild_id is not None
		is_admin= global_admins and any(payload.user_id == global_admins[x] for x in global_admins)

		if is_dm or is_admin:
			pass
		else:
			guild= self.bot.get_guild(payload.guild_id)
			if user.id == guild.owner.id:
				pass
			else:
				return

		await func(self, payload)

	return dec

def check_self(func):
	async def dec(self, payload):
		channel= self.bot.get_channel(payload.channel_id)
		message= await channel.fetch_message(payload.message_id)

		# check that message is from self
		if not message.author == self.bot.user:
			return

		await func(self,payload)

	return dec