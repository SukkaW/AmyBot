from discord.ext import commands
import json, utils, yaml

class PartialCommand(commands.Command):
	def __init__(self, func, short, *args, **kwargs):
		self.short= short
		super().__init__(func, *args, **kwargs)


async def handle_general_error(ctx, error_name, **kwargs):
	ERROR_STRINGS= yaml.safe_load(open(utils.ERROR_STRING_FILE))

	name= error_name.replace("_template", "")
	template_name= f"{error_name}_template"

	if template_name not in ERROR_STRINGS:
		available= [x for x in ERROR_STRINGS if x.endswith("template")]
		return utils.render(ERROR_STRINGS['tmp_not_found_template'], dict(NAME=name, AVAILABLE=available))

	await ctx.send(utils.render(ERROR_STRINGS[template_name], kwargs))


def parse_keywords(query, keywords, aliases=None, reps=None):
	"""
	Converts string such as "blah keywordval" into { "keyword": val }.

	:param query: String containing 0 or more keywords
	:param keywords: Dictionary of keyword : parsing function. If keyword is found and parsing function is not None, parsing function is applied to value found
	:param aliases: Dictionary of keyword : list of aliases
	:param reps: Dictionary of x : list y. Replace all substrings in query that are outlined in list y with string x.
	:return: Dictionary containing query with keywords removed and dictionary of keyword : parsed value
	"""
	ret= {"keywords": {}, "clean_query": None}

	# perform replacements (start-only)
	split= [x.lower() for x in query.split()]
	if reps:
		for x in reps:
			for y in reps[x]:
				for i in range(len(split)):
					if split[i].startswith(y): split[i]= split[i].replace(y,x)

	# inits
	inds= [] # track matching words to remove later
	keywords= {k.lower() : v for k,v in keywords.items()}
	aliases= {k.lower() : [x.lower() for x in v] for k,v in aliases.items()}

	# search for keywords
	for k in keywords:
		match= None

		# Look for matching keyword
		for i,x in enumerate(split):
			if x.startswith(k):
				match= (i,x,k)
			elif k in aliases:
				for a in aliases[k]:
					if x.startswith(a):
						match= (i,x,a)
						break

			if match: break

		# Parse value with callable supplied by keywords[k]
		if match and match[0] not in inds:
			val= match[1].replace(match[2],"")
			if keywords[k] is not None:
				try:
					val= keywords[k](val)
				except Exception as e:
					raise ParseError(keyword=k, value=val, exception=e)

			inds.append(match[0])
			ret['keywords'][k]= val

	# clean up query
	inds.sort(reverse=True) # remove largest indices first
	tmp= query.split()
	for i in inds:
		del tmp[i]
	ret['clean_query']= " ".join(tmp)

	return ret

def render_parse_error(ctx, parse_error):
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

	return utils.render(ERROR_STRINGS['usage_template'], reps)

# Parses for keywords, but also handles errors.
async def handle_keywords(ctx, keys, aliases=None, reps=None):
	try:
		tmp= parse_keywords(ctx.query, keys, aliases=aliases, reps=reps)
		return tmp
	except ParseError as e:
		text= render_parse_error(ctx, e)
		await ctx.send(f"{text}")
		return False

class ParseError(Exception):
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

	def __str__(self):
		STRINGS= yaml.safe_load(open(utils.ERROR_STRING_FILE))
		reps= {
			"VALUE": self.value,
			"KEYWORD": self.keyword,
			"EXCEPTION": str(self.exception)
		}
		return utils.render(STRINGS['parse_console_template'], reps)


# ---- Parsing Functions ----
# Invalid values should raise an Exception with a reason supplied to the constructor
# Don't capitalize first word because this string is inserted in the message printed by ParseError

def int_to_price(x, numDec=1):
	sx= str(x)

	if len(sx) > 6: sx= sx[:-6] + "." + sx[-6:][:numDec] + "m"
	elif len(sx) > 3: sx = sx[:-3] + "." + sx[-3:][:numDec] + "k"

	if "." in sx:
		while sx[-2] == '0': sx= sx[:-2] + sx[-1]
		if sx[-2]== ".": sx =sx[:-2] + sx[-1]

	return sx

def price_to_int(x):
	x= str(x)

	ix = (x.lower().replace("k", "000").replace("m", "000000"))
	if "." in x:
		numDec = len(str(x).replace("k","").replace("m","").split(".")[1])
		ix = ix[:-numDec].replace(".", "")

	return to_int(ix)

def to_int(val):
	STRINGS= yaml.safe_load(open(utils.ERROR_STRING_FILE))

	if val.strip() == "":
		raise Exception(STRINGS['int_reasons']['empty'])

	try: return int(val)
	except ValueError: raise Exception(STRINGS['int_reasons']['not_int'])

def to_pos_int(val):
	STRINGS= yaml.safe_load(open(utils.ERROR_STRING_FILE))

	ret= price_to_int(val)
	if ret < 0: raise Exception(STRINGS['int_reasons']['negative'])
	return ret

def to_bool(val, empty=True):
	if str(val) == "": return empty
	else: return bool(val)

