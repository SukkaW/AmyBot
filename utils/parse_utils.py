from discord.ext.commands import CommandError
import utils

class KeywordList:
	def __init__(self, keywords):
		self.keywords= keywords

	def __iter__(self):
		return (x for x in self.keywords)

	def __getitem__(self, key):
		for x in self.keywords:
			if key.lower() in [x.name] + x.aliases:
				return x

	def __contains__(self, item):
		for x in self.keywords:
			if isinstance(item,str) and item.lower() in [x.name] + x.aliases:
				return True
			if isinstance(item,Keyword) and item in self.keywords:
				return True
		return False

	def __delitem__(self, instance):
		for x in self.keywords:
			if x.name == instance:
				tmp= x
				break
		else: return
		self.keywords.remove(tmp)

class Keyword:
	def __init__(self, name, parsing_function=None, aliases=None):
		self.name= name
		self.__dict__['value']= None
		self.has_value= False

		if parsing_function is None: # default parsed value type is string
			self.parsing_function= lambda x: str(x)
		else:
			self.parsing_function= parsing_function

		if aliases is None:
			self.aliases= []
		else:
			self.aliases= aliases

	# force lower-case
	def __setattr__(self, key, value):
		if key in ['name']:
			self.__dict__[key]= value.lower()
		elif key in ['aliases']:
			self.__dict__[key]= [x.lower() for x in value]
		elif key in ['value']:
			self.__dict__['has_value']= True
			self.__dict__['value']= value
		else:
			self.__dict__[key]= value

	def __bool__(self):
		return bool(self.value) and self.has_value

	# for debug purposes
	def __str__(self):
		return f"Keyword [{self.name}] {'has value [{}]'.format(self.value) if self.has_value else 'has no value.'}"

	# split key and val (eg min30k --> 30k) and apply parsing function
	def get_val(self, string):
		to_chk= [self.name] + self.aliases
		to_chk.sort(key=lambda x: len(x), reverse=True) # check longest first

		for x in to_chk:
			if string.startswith(x):
				tmp= string.replace(x,"",1)
				self.value= self.parsing_function(tmp)
				return self.value

		return None

def parse_keywords(query, keywords):
	"""
	Converts string such as "blah keywordval" into { "keyword": val }.

	:param query: String containing 0 or more keywords
	:param keywords: Dictionary of keyword : parsing function. If keyword is found and parsing function is not None, parsing function is applied to value found
	:param aliases: Dictionary of keyword : list of aliases
	:param reps: Dictionary of x : list y. Replace all substrings in query that are outlined in list y with string x.
	:return: Dictionary containing query with keywords removed and dictionary of keyword : parsed value
	"""
	# inits
	split= [x.lower() for x in query.split()]
	inds= [] # marks words in query to remove later

	# search for keywords
	# if duplicate keywords in query, only last value used
	for k in keywords:
		for i,x in enumerate(split):
			if k.get_val(x):
				inds.append(i)

	# clean up query
	inds.sort(reverse=True)
	for i in inds:
		split.pop(i)

	return " ".join(split), keywords

class ParseError(CommandError):
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

	def render(self, ctx):
		COG_STRINGS= utils.load_yaml(utils.COG_STRING_FILE)
		ERROR_STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)

		reps= {
			"PREFIX": ctx.prefix,
			"COMMAND": ctx.command.name,
			"ARGS": COG_STRINGS[ctx.command.cog.qualified_name]['commands'][ctx.command.name]['args'],
			"VALUE": self.value,
			"KEYWORD": self.keyword,
			"EXCEPTION": str(self.exception)
		}

		return utils.render(ERROR_STRINGS['usage_template'], reps)

	def __str__(self):
		STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)
		reps= {
			"VALUE": self.value,
			"KEYWORD": self.keyword,
			"EXCEPTION": str(self.exception)
		}
		return utils.render(STRINGS['parse_console_template'], reps)


# ---- Parsing Functions ----
# Invalid values should raise an Exception with a reason supplied to the constructor
# These exceptions are then wrapped into a ParseError

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

	if val.strip() == "":
		STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)
		raise Exception(STRINGS['int_reasons']['empty'])

	try:
		return int(val)
	except ValueError:
		STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)
		raise Exception(STRINGS['int_reasons']['not_int'])

def to_pos_int(val):
	ret= price_to_int(val)
	if ret < 0:
		STRINGS= utils.load_yaml(utils.ERROR_STRING_FILE)
		raise Exception(STRINGS['int_reasons']['negative'])
	return ret

def to_bool(val, empty=True):
	if str(val) == "": return empty
	else: return bool(val)

# hacky-workaround for parsing the alias "20" properly
# eg any in [date2019, 2019, year2019] will parse to 2019
def to_date(val):
	if val.startswith("20"): pass
	else: val= "20" + val

	return to_pos_int(val)

def get_date_key(): return Keyword("date", to_date, aliases=["year", "20", "year20"])