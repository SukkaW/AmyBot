class Column:
	def __init__(self, data, header="", is_link=False, max_width=None):
		self.data= [str(x) for x in data]
		self.orig_data= [str(x) for x in data]
		self.header= header
		self.is_link= is_link # If true, column will not use a header nor be code-wrapped

		self.max_width= max(len(header), max([len(str(x)) for x in data])) # get max_width from data
		self._limit_request= max_width
		if self._limit_request is not None: self.max_width= min(int(self._limit_request), self.max_width) # reduce max_width if specified

		for i in range(len(self.data)):
			if len(self.data[i]) > self.max_width:
				self.data[i]= self.data[i][:self.max_width-3] + "..."

		self._is_init= True


	def __iter__(self):
		return self.data

	def __len__(self):
		return len(self.data)

	def __getitem__(self, ind):
		return self.data[ind]

	def __setattr__(self, key, value):
		self.__dict__[key]= value


		if "_is_init" in self.__dict__ and self.__dict__['_is_init']:
			if key == "max_width":
				self.__dict__['_limit_request']= value

			# recalculate max width and truncations
			self.__dict__['max_width']= max(len(self.header), max([len(str(x)) for x in self.data]))
			if self._limit_request is not None:
				self.__dict__['max_width']= min(int(self._limit_request), self.max_width)

			for i in range(len(self.orig_data)):
				if len(self.data[i]) > self.max_width:
					self.__dict__['data'][i]= self.data[i][:self.max_width-3] + "..."


def pprint(columns, prefix="", suffix="", code=None, v_sep="|", h_sep="-", v_pad=1):
	ret= ""

	padding= "".join([" "]*v_pad)
	v_sep= padding + v_sep + padding

	not_link= [x for x in columns if not x.is_link]
	is_link= [x for x in columns if x.is_link]
	single_tick= (len(is_link) != 0)

	assert all([len(columns[0]) - len(x) == 0 for x in columns[1:]]) # check all columns same length
	assert len(not_link) > 0

	if code and not single_tick: ret+= f"```{code}\n"
	if prefix: ret+= prefix + "\n"

	if any(x.header for x in columns):
		# headers
		tmp= ""
		for col in not_link:
			tmp+= col.header.ljust(col.max_width) + v_sep
		if single_tick: tmp= f"`{tmp}`"
		ret+= tmp + "\n"

		h_sep_length= sum(x.max_width for x in not_link) + len(not_link)*len(v_sep)
		if h_sep: ret+= "".join(["-"]*h_sep_length) + "\n" # horizontal divider

		# data
		for i in range(len(not_link[0])):
			tmp= ""
			for col in not_link:
				tmp+= col[i].ljust(col.max_width) + v_sep
			if single_tick: tmp= f"`{tmp}`"

			for col in is_link:
				tmp+= col[i].ljust(col.max_width) + padding + padding

			ret+= tmp + "\n"

	if suffix: ret+= suffix + "\n"
	if code and not single_tick: ret+= f"\n```"
	return ret


def break_tables(tables, max_len=1900, no_orphan=4, join_char="\n"):
	pages= []
	split= [x.split("\n") for x in tables]

	page_len= lambda pg: sum(len(x) for x in pg) + len(pg)
	jlen= len(join_char)

	pg= []
	for i in range(len(split)):
		tbl= split[i]

		for j in range(len(tbl)):
			line= tbl[j]

			if j == 0: # if at new table, look ahead to make sure no orphans
				lines_next= pg[i : i+no_orphan]
				length_next= sum(len(x) for x in lines_next) + len(lines_next)*jlen
				if page_len(pg) + length_next <= max_len:
					pg.append(line)
				else:
					pages.append(pg)
					pg= [line]
			elif page_len(pg) + len(line) + jlen <= max_len:
				pg.append(line)
			else:
				pages.append(pg)
				pg= [line]

	if pg: pages.append(pg)
	return [join_char.join(x) for x in pages]


if __name__ == "__main__":
	import random

	cols= []
	for i in range(2):
		cols.append(Column(data=[random.randint(10*(10**i), 100*(10**i)) for j in range(10)], header=f"{i} blah"))
	cols.append(Column(data= [122313, 463]*5, is_link=True))
	cols.append(Column(data= [123, 4563]*5, is_link=True))

	print(pprint(cols, prefix="prefix", suffix="suffix"))