import utils, yaml, jinja2


# class HotSwapMixin:
# 	# Replaces variable names in strings with appropriate value, eg "%PREFIX%" --> self.clean_prefix
# 	@staticmethod
# 	def _clean(text, escape_char, reps=None):
# 		if reps is None: reps= {}
# 		def wrap(x): return escape_char + x + escape_char
#
# 		for x in reps:
# 			if reps[x] == "": reps[x]= "(empty)"
# 			text= text.replace(wrap(x), reps[x])
#
# 		return text
#
# 	# Get usage string for errors
# 	# Should be called from an instance of a Command belonging to an instance of a Cog
# 	@staticmethod
# 	def _get_usage(ctx, parse_error):
# 		COG_STRINGS= json.load(open(utils.COG_STRING_FILE))
# 		ERROR_STRINGS= json.load(open(utils.ERROR_STRING_FILE))
#
# 		reps= {
# 			"PREFIX": ctx.prefix,
# 			"COMMAND": ctx.invoked_with,
# 			"ARGS": COG_STRINGS[ctx.command.cog.qualified_name]['commands'][ctx.command.name]['args'],
# 			"VALUE": parse_error.value,
# 			"KEYWORD": parse_error.keyword,
# 			"EXCEPTION": str(parse_error.exception)
# 		}
#
# 		return HotSwapMixin._clean(ERROR_STRINGS['usage_template'], ERROR_STRINGS['escape_char'], reps)

def get_usage(ctx, parse_error):
	COG_STRINGS= yaml.safe_load(open(utils.COG_STRING_FILE))
	ERROR_STRINGS= yaml.safe_load(open(utils.ERROR_STRING_FILE))

	reps= {
		"PREFIX": ctx.prefix,
		"COMMAND": ctx.invoked_with,
		"ARGS": COG_STRINGS[ctx.command.cog.qualified_name]['commands'][ctx.command.name]['args'],
		"VALUE": parse_error.value,
		"KEYWORD": parse_error.keyword,
		"EXCEPTION": str(parse_error.exception)
	}

	return jinja2.Template(ERROR_STRINGS['usage_template']).render(**reps)