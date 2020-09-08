import utils.cog_utils as cmd
from utils.pprint_utils import Column, pprint
from utils.misc_utils import contains
import json, utils

""" NOTE: find_items and to_table should be able to handle the same keywords """
# 	@TODO: keys - thread

# Potentially valuable suffix / prefixes
def is_rare(name):
	rares= ["Slaughter", "Savage", "Mystic", "Shielding", "Charged", "Frugal", "Radiant"]
	return any(x.lower() in name.lower() for x in rares)

# supported keys: 	min, max, year, sell, buy, rare, norare
#	 (no effect):   link
def find_items(name, keywords=None):
	# inits
	ret= {}
	data= json.load(open(utils.AUCTION_FILE))
	if keywords is None: keywords= {}

	# if keyword passed in, use it to filter results
	eq_checks= { "min": lambda x: int(x['price']) >= keywords['min'],
			  "max": lambda x: int(x['price']) <= keywords['max'],
			  "year": lambda x: int(x['date'][2]) >= keywords['year'],
			  "seller": lambda x: x['seller'].lower() == keywords['sell'].lower(),
			  "buyer": lambda x: x['buyer'].lower() == keywords['buy'].lower(),
			}
	eq_checks= [eq_checks[x] for x in eq_checks if x in keywords]

	name_checks= {
		"rare": lambda x: is_rare(x),
		"norare": lambda x: not is_rare(x)
	}
	name_checks= [name_checks[x] for x in name_checks if x in keywords]

	# get items containing [name] and passing all keyword checks
	for eq_name in data:
		if not contains(to_search=eq_name, to_find=name): continue
		if not all(chk(eq_name) for chk in name_checks): continue

		for eq in data[eq_name]:
			if all(chk(eq) for chk in eq_checks):
				if eq_name not in ret:
					ret[eq_name]= []
				ret[eq_name].append(eq)

	return ret


# convert equip results to a table (string) to print
# certain columns are only printed if a relevant keyword is passed in
# supported keys: 	sell, buy, link
#    (no effect): 	min, max, year, rare, norare
def to_table(eq_name, eq_list, keywords):
	# inits
	CONFIG= utils.load_yaml(utils.PPRINT_CONFIG)['auction']
	eq_list.sort(reverse=True, key=lambda x: int(x['price']))

	header_dict= CONFIG['headers']
	default_cols= CONFIG['default_cols']
	keyword_cols= CONFIG['keyword_cols']

	has_link= "link" in keywords and keywords['link']
	has_thread= "thread" in keywords and keywords['thread']

	# get data for cols to print
	cols= []
	col_names= default_cols + [keyword_cols[x] for x in keyword_cols if x in keywords]
	for x in col_names:
		# @TODO: handle key-errors

		data= [eq[x] for eq in eq_list]
		c= Column(data=data, header=header_dict[x])

		if x == "stats": c.max_width= CONFIG['stat_col_width']
		if x == "price": c.data= [str(cmd.int_to_price(x)) for x in c.data]

		cols.append(c)

	# add date col
	data= []
	for x in eq_list:
		data.append(f"#{x['type'][0].upper()}{x['auction_number']} / {x['date'][1]}-{x['date'][2]}")
	cols.append(Column(data=data, header=header_dict['year']))

	# add link col
	if has_link:
		cols.append(Column(data=[x['link'] for x in eq_list], header=header_dict['link'], is_link=True))

	if has_link or has_thread:
		return pprint(columns=cols, prefix=f"**{eq_name}**", code="") # add single ticks

	return pprint(columns=cols, prefix=f"@ {eq_name}", code=None) # we'll add code-blocks later


if __name__ == "__main__":
	from utils import cog_utils
	from cogs import auction_cog
	from utils import pprint_utils

	query= "peerl surtr 2019 link"
	try:
		parsed= cog_utils.parse_keywords(query,
										   keywords=auction_cog.base_keys,
										   aliases=auction_cog.base_aliases,
										   reps=auction_cog.base_reps)
	except cog_utils.ParseError as e:
		print(e)
	else:
		items= find_items(parsed['clean_query'], parsed['keywords'])
		tables= [to_table(x, items[x], keywords=parsed['keywords']) for x in items]
		pages= pprint_utils.break_tables(tables, max_len=1950)

		for x in pages: print(f"```py\n{x}\n```")