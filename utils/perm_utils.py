from discord.ext import commands
import utils, os, copy

def check_perms(ctx):
	# inits
	GLOBALS= utils.load_yaml(utils.GLOBAL_PERMS_FILE)
	cmd= ctx.command.name
	cog= ctx.cog.qualified_name if ctx.cog is not None else "none"

	# check global admin
	if _is_global_admin(ctx, GLOBALS):
		return True

	if ctx.guild is None: # if dm, check dm perms
		ret= _check(cmd=cmd, cog=cog, perm_dict=GLOBALS['dm'], flags=GLOBALS['flags'], ctx=ctx, is_dm=True)
		utils.dump_yaml(GLOBALS, utils.GLOBAL_PERMS_FILE)
	else:
		# load guild perms
		perms_file= f"{utils.PERMS_DIR}{str(ctx.guild.id)}.yaml"
		if os.path.exists(perms_file):
			perms_dict= utils.load_yaml(perms_file)
		else:
			perms_dict= GLOBALS['default_perms']
			utils.dump_yaml(perms_dict, perms_file)

		# check guild perms
		ret= _check(cmd=cmd, cog=cog, perm_dict=perms_dict, flags=perms_dict['flags'], ctx=ctx, is_dm=False)
		utils.dump_yaml(perms_dict, perms_file)

	return ret

# do checks, starting with smallest scope
def _check(cmd, cog, perm_dict, flags, ctx, is_dm=False):
	# inits
	default_dict= dict(everyone=flags['PASS'], exceptions=[]) # @TODO: use flag reference
	chks= {
		"user": lambda dct: ctx.author.id in dct['user'],
		"roles": lambda dct: all(y in [x.id for x in ctx.author.roles] for y in dct['roles']),
		"channel": lambda dct: ctx.channel.id in dct['channel'],
	}
	def flag_chk(val):
		if val == flags['ALLOW']: return True
		elif val == flags['FAIL']: return False
		elif val == flags['PASS']: return None

	if is_dm: keys= ['user']
	else: keys= ['user', 'role', 'channel']

	silent= not perm_dict['vocal_fail']
	details= perm_dict['details']


	# make if missing
	if cog not in perm_dict: perm_dict[cog]= copy.deepcopy(default_dict)
	if cmd not in perm_dict[cog]: perm_dict[cog][cmd]= copy.deepcopy(default_dict)

	# cmd checks
	for i,dct in enumerate([perm_dict[cog][cmd], perm_dict[cog], perm_dict]): # loop levels
		for e in dct['exceptions']: # loop exception list
			if all(chks[k](e) for k in keys): # check user / role / channel id listed in expception

				# if allowed return True, if fail raise PermissionFailure, else move to next level
				tmp= flag_chk(e['value'])
				if tmp is True:
					return tmp
				elif tmp is False:
					raise PermissionFailure(cmd, cog, exception=e, level=i, is_dm=is_dm, silent=silent, details=details)
				else: pass

		# if no matching exceptions, check "everyone" flag for current level
		if (tmp:=flag_chk(dct['everyone'])) is not None:
			if tmp is False: raise PermissionFailure(cmd, cog, level=i, everyone=True, is_dm=is_dm, silent=silent, details=details)
			return tmp

	raise PermissionFailure(cmd, cog, level=PermissionFailure.DEFAULT_LEVEL, is_dm=is_dm, silent=silent, details=details)


def _is_global_admin(ctx, GLOBALS):
	global_admins= GLOBALS['admins']
	if global_admins and any(ctx.author.id == global_admins[x] for x in global_admins):
		return True
	return False

class PermissionFailure(commands.CheckFailure):
	SERVER_LEVEL= 2
	COG_LEVEL= 1
	COMMAND_LEVEL= 0
	DEFAULT_LEVEL= -1

	# Init with everyone set to True if the permission failure was due to the perm_dict's everyone key being false.
	def __init__(self, command, cog, level, exception=None, everyone=False, is_dm=False, silent=True, details=False):
		self.cog= cog
		self.command= command
		self.exception= exception
		self.level= level
		self.everyone= everyone
		self.is_dm= is_dm
		self.silent= silent
		self.details= details

	def render(self):
		STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)

		if self.level == self.DEFAULT_LEVEL:
			return utils.render(STRINGS['default_perm_error'], self.__dict__)
		if self.level == self.SERVER_LEVEL:
			return utils.render(STRINGS['server_perm_error'], self.__dict__)
		else:
			return utils.render(STRINGS['command_or_cog_perm_error'], self.__dict__)
