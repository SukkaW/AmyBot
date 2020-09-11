# @todo clean up Column.setattr
class Column:
	def __init__(self, data, header="", trailer="", is_link=False, max_width=None):
		self.header= str(header)
		self.trailer= str(trailer)
		self.is_link= is_link # If true, column will not use a header nor be code-wrapped

		self.max_width= None # so the ide stops complaining
		self.__dict__['max_width']= max(len(self.header), len(self.trailer), max([len(str(x)) for x in data])) # get max_width from data
		self._limit_request= None

		self.data= []
		self.orig_data= data

	def __iter__(self):
		return self.data

	def __len__(self):
		return len(self.data)

	def __getitem__(self, ind):
		return self.data[ind]

	# @todo: handle modifications to specific data indices (eg Column.data[1]) via data wrapper class
	def __setattr__(self, key, value):
		if key in ['data', 'orig_data', 'max_width']:
			if key in ['orig_data', 'data']:
				if not value:
					self.__dict__['orig_data']= []
					self.__dict__['data']= self.__dict__['orig_data'].copy()
					return
				else:
					self.__dict__['orig_data']= value
					self.__dict__['data']= [str(x) for x in value]
			elif key == "max_width":
				if value is None: return
				self.__dict__['_limit_request']= value

			# recalculate max width and truncations
			self.__dict__['max_width']= max(len(self.header), len(self.trailer), max([len(str(x)) for x in self.data]))
			if self._limit_request is not None:
				self.__dict__['max_width']= min(int(self._limit_request), self.max_width)

			if self._limit_request:
				for i in range(len(self.orig_data)):
					if len(self.data[i]) > self._limit_request:
						self.__dict__['data'][i]= self.data[i][:self.max_width-3] + "..."

		else:
			self.__dict__[key]= value

# Basically a list of columns
class Table:
	def __init__(self, columns):
		self.columns= columns

# @ todo: comment this
def pprint(columns, prefix="", suffix="", code=None, v_sep="|", h_sep="-", v_pad=1):
	ret= ""

	columns= columns.columns if isinstance(columns, Table) else columns
	padding= "".join([" "]*v_pad)
	v_sep= padding + v_sep + padding

	not_link= [x for x in columns if not x.is_link]
	is_link= [x for x in columns if x.is_link]
	single_tick= (len(is_link) != 0)

	assert all([len(columns[0]) - len(x) == 0 for x in columns[1:]]) # check all columns same length
	assert len(not_link) > 0

	if code is not None and not single_tick: ret+= f"```{code}\n"
	if prefix: ret+= prefix + "\n"

	# horiz separator for header
	if h_sep:
		h_sep_length= sum(x.max_width for x in not_link) + len(not_link)*len(v_sep)
		h_sep= "".join(["-"]*h_sep_length)
		if single_tick: h_sep= f"`{h_sep}`"

	# headers
	if any(x.header for x in columns):
		tmp= ""
		for col in not_link:
			tmp+= col.header.ljust(col.max_width) + v_sep
		if single_tick: tmp= f"`{tmp}`"

		ret+= tmp + "\n"
		if h_sep: ret+= h_sep + "\n"

	# data
	for i in range(len(not_link[0])):
		tmp= ""
		for col in not_link:
			tmp+= col[i].ljust(col.max_width) + v_sep
		if single_tick: tmp= f"`{tmp}`"

		for col in is_link:
			tmp+= col[i].ljust(col.max_width) + padding + padding

		ret+= tmp + "\n"

	# trailers
	if any(x.trailer for x in columns):
		tmp= ""
		if h_sep: ret+= h_sep + "\n"

		for col in not_link:
			tmp+= col.trailer.ljust(col.max_width) + v_sep
		if single_tick: tmp= f"`{tmp}`"

		ret+= tmp + "\n"


	if suffix: ret+= suffix + "\n"
	if code is not None and not single_tick: ret+= f"\n```"
	return ret


# Groups strings into a new list of "pages" such that each page
#    has length < max_len
#    has either exactly 0 or greater than no_orphan lines of each string
def get_pages(strings, max_len=1900, no_orphan=4, join_char="\n"):
	# inits
	if not isinstance(strings, list):
		strings= [strings]

	pages= []
	split= [x.split("\n") for x in strings]

	jlen= len(join_char)
	def page_len(lst): # calculate length of a page, accounting for join_char length
		return sum(len(x) for x in lst) + len(lst)*jlen

	pg= []
	for i in range(len(split)): # loop each message
		tbl= split[i]

		for j in range(len(tbl)): # loop each line in message
			line= tbl[j]

			# if new_page, check if enough space for adding no_orphan lines to current page
			next_len= page_len(pg) + page_len(tbl[:no_orphan])
			will_orphan= (j == 0 and next_len > max_len)

			# check if enough space for current line
			will_exceed= (page_len(pg) + len(line) + jlen > max_len)

			if will_orphan or will_exceed:
				pages.append(pg)
				pg= [line]
			else:
				pg.append(line)

	if pg: pages.append(pg)
	return [join_char.join(x) for x in pages]
