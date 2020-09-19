from utils.parse_utils import contains, int_to_price
from classes.errors import TemplatedError
import utils.pprint_utils as Pprint
import utils


async def pageify_and_send(ctx, strings, CONFIG, has_link=False, max_len=1900):
	# group strings into pages
	pages= Pprint.get_pages(strings, max_len=max_len)

	# send pages
	await send_pages(ctx, pages, has_link=has_link, code="py" if not has_link else None,
					 page_limit_dm=CONFIG['page_limit_dm'],
					 page_limit_server=CONFIG['page_limit_server'])

def check_for_key(key, keywords, col_names):
		return keywords[key] or 'key' in col_names


def stringify_tables(tables, has_link=False, header_func=None, trailer_func=None, code=""):
	# convert tables to strings
	table_strings= []
	for x in tables:
		suffix= trailer_func(x) if trailer_func is not None else ""

		# If link and no code block explicitly requested, format header for single ticks
		if has_link and code == "":
			prefix= f"**{header_func(x)}**" if header_func is not None else ""
		else:
			prefix= f"@ {header_func(x)}" if header_func is not None else ""

		# If link, format table for single ticks
		if has_link:
			# add single ticks
			table_strings.append(Pprint.pprint(x, prefix=prefix, code=code, suffix=suffix))
		else:
			# we'll add code-blocks later
			table_strings.append(Pprint.pprint(x, prefix=prefix, code=None, suffix=suffix))

	return table_strings


# @ todo: check max length (2000)
# send to discord, enforcing a page limit and optionally wrapping in code blocks
async def send_pages(ctx, pages, code=None, page_limit_server=2, page_limit_dm=None, has_link=False, prefix="", suffix=""):
	# code blocks
	if code:
		pages= [f"```{code}\n{x}\n```" for x in pages]

	# append "# pages omitted" warning
	limit= page_limit_server if ctx.guild is not None else page_limit_dm
	if len(pages) > limit:
		STRINGS= utils.load_yaml(utils.PPRINT_STRING_FILE)
		dct= {
			"PAGES": pages,
			"PAGE_LIMIT": limit,
			"HAS_LINK": has_link
		}
		omit_string= utils.render(STRINGS['omit_template'], dct)
		pages[limit-1]+= omit_string

	# prefix / suffix
	pages[0]= prefix + pages[0]
	pages[-1]= pages[-1] + suffix

	# send
	for x in pages[:limit]:
		await ctx.send(x)


def get_summary_table(lst, CONFIG, name_key="name", price_key="price"):
	# inits
	groups= CONFIG['summary_groups']
	header_dict= CONFIG['summary_headers']

	# tallies
	values,counts= {},{}
	for x in groups:
		values[x]= 0
		counts[x]= 0

	unknown= [0,0]
	for x in lst:
		matched= False
		for y in groups:
			for z in groups[y]:
				if contains(to_search=x[name_key], to_find=z):
					counts[y]+= 1
					values[y]+= int(x[price_key])
					matched= True
					break

		if not matched:
			unknown[0]+= 1
			unknown[1]+= int(x[price_key])


	# sum tallies
	total_count= sum(counts.values())
	total_value= int_to_price(sum(values.values()))

	# convert to lists
	vals= [int_to_price(values[x]) for x in groups]
	cnts= [counts[x] for x in groups]

	if unknown[0]:
		vals.append(int_to_price(unknown[1]))
		cnts.append(unknown[0])
		groups[header_dict['unknown']] = []

	return Pprint.Table([
		Pprint.Column(data=groups, header=header_dict['category'], trailer=header_dict['total']),
		Pprint.Column(data=cnts, header=header_dict['total_count'], trailer=total_count),
		Pprint.Column(data=vals, header=header_dict['total_credits'], trailer=total_value),
	])

def filter_data(checks, data, keyword_list):
	ret= []

	# get items containing [name] and passing all keyword checks
	if not checks: raise TemplatedError("no_keywords", keywords=keyword_list)
	for x in data:
		if all(chk(x) for chk in checks):
			ret.append(x)

	if not ret: raise TemplatedError("no_equip_match", keywords=keyword_list)
	return ret

def get_cols(data, special_cols, col_names, CONFIG, format_rules=None):
	# inits
	if format_rules is None: format_rules= {}
	header_dict= CONFIG['equip_headers']

	# @TODO: handle key-errors
	# create columns
	cols= []
	for x in col_names:
		if x in special_cols: continue # these are handled later

		# create col
		d= [eq[x] for eq in data]
		c= Pprint.Column(data=d, header=header_dict[x])

		# special formatting
		if x in format_rules:
			c= format_rules[x](c)

		cols.append(c)

	return cols

def get_col_names(default_cols, keyword_list, key_map):
	# get keys to pull data from
	col_names= default_cols
	for x in keyword_list:
		if not x or x.name not in key_map or key_map[x.name] in col_names:
			continue
		col_names.append(key_map[x.name])
	return col_names

def categorize(lst, key_name):
		# categorize
		cats= {}
		for x in lst:
			if x[key_name] not in cats:
				cats[x[key_name]]= []
			cats[x[key_name]].append(x)

		return cats