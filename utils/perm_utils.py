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

	# make if missing
	if cog not in perm_dict: perm_dict[cog]= copy.deepcopy(default_dict)
	if cmd not in perm_dict[cog]: perm_dict[cog][cmd]= copy.deepcopy(default_dict)

	# cmd checks
	for dct in [perm_dict[cog][cmd], perm_dict[cog], perm_dict]: # loop levels
		for e in dct['exceptions']: # loop exception list
			if all(chks[k](e) for k in keys): # if applicable exception, return exception value
				if (tmp:=flag_chk(e['value'])) is not None:
					return tmp

		# check "everyone" flag for current level
		if (tmp:=flag_chk(dct['everyone'])) is not None:
			return tmp

	return False


def _is_global_admin(ctx, GLOBALS):
	global_admins= GLOBALS['admins']
	if global_admins and any(ctx.author.id == global_admins[x] for x in global_admins):
		return True
	return False

class PermissionFailure(commands.CheckFailure):
	def __init__(self):
		pass