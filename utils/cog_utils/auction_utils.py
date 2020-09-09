from utils.parse_utils import int_to_price
from utils.pprint_utils import Column, Table
from utils.misc_utils import contains
from utils.error_utils import TemplatedError
import json, utils

""" NOTE: find_items and to_table should be able to handle the same keywords """
# 	@TODO: keys - thread

# Potentially valuable suffix / prefixes
def is_rare(name):
	rares= ["Slaughter", "Savage", "Mystic", "Shielding", "Charged", "Frugal", "Radiant"]
	return any(x.lower() in name.lower() for x in rares)


# Returns dict -- each key is an equip name -- each value is a list of dicts (sale data)
# supported keys: 	min, max, year, sell, buy, rare, norare
#	 (no effect):   link
def find_equips(keyword_list):
	# inits
	ret= []
	data= json.load(open(utils.AUCTION_FILE))

	# if keyword passed in, use it to filter results
	checks= {
		"min": lambda x: int(x['price']) >= keyword_list['min'].value,
		"max": lambda x: int(x['price']) <= keyword_list['max'].value,
		"date": lambda x: int(x['date'][2]) >= keyword_list['date'].value,
		"seller": lambda x: x['seller'].lower() == keyword_list['sell'].value.lower(),
		"buyer": lambda x: x['buyer'].lower() == keyword_list['buy'].value.lower(),
		'name': lambda x: contains(to_search=x['name'], to_find=keyword_list['name'].value),
		"rare": lambda x: is_rare(x['name'].value),
		"norare": lambda x: not is_rare(x['name'].value)
	}
	checks= [checks[x] for x in checks if x in keyword_list and keyword_list[x].has_value]

	# get items containing [name] and passing all keyword checks
	if not checks: raise Exception#raise TemplatedError("no_keywords", keywords=keyword_list) # @todo
	for x in data:
		if all(chk(x) for chk in checks):
			ret.append(x)

	if not ret: raise TemplatedError("no_equip_match", keywords=keyword_list)
	return ret


# @ todo: what if multiple base_keys point to same eq_data key
# convert equip results to a table (string) to print
# certain columns are only printed if a relevant keyword is passed in (see key_maps)
def to_table(command, eq_list, keyword_list, default_col_name="default_cols"):
	# inits
	CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)
	eq_list.sort(reverse=True, key=lambda x: int(x['price']))

	header_dict= CONFIG['equip_headers']
	default_cols= CONFIG[command][default_col_name]
	key_map= CONFIG['key_map']
	special_cols= ['thread', 'link', 'date'] # these have to be added last for formatting reasons

	# get keys to pull data from
	col_names= default_cols
	for x in keyword_list:
		if not x or x.name in col_names or x.name not in key_map:
			continue
		else:
			col_names.append(key_map[x.name])

	# @TODO: handle key-errors
	# create columns
	cols= []
	for x in col_names:
		if x in special_cols: continue # these are handled later

		# create col
		data= [eq[x] for eq in eq_list]
		c= Column(data=data, header=header_dict[x])

		# special formatting
		if x == "stats":
			c.max_width= CONFIG[command]['stat_col_width']
		if x == "price":
			c.data= [str(int_to_price(x)) for x in c.data]

		cols.append(c)

	# add date col
	if 'date' in col_names:
		data= []
		for x in eq_list:
			data.append(f"#{x['type'][0].upper()}{x['auction_number']} / {x['date'][1]}-{x['date'][2]}") # todo: template
		cols.append(Column(data=data, header=header_dict['date']))

	# add link col
	if 'link' in col_names:
		cols.append(Column(data=[x['link'] for x in eq_list], header=header_dict['link'], is_link=True))

	# add thread col
	# @TODO

	return Table(cols)


if __name__ == "__main__":
	from utils import pprint_utils, parse_utils
	from cogs import auction_cog

	query= "peerl surtr 2019 link"
	parsed= parse_utils.parse_keywords(query,
									   keywords=auction_cog.base_keys,
									   aliases=auction_cog.base_aliases,
									   reps=auction_cog.base_reps)

	items= find_equips(parsed['clean_query'], parsed['keywords'])
	tables= [to_table("auction", x, items[x], keyword_list=parsed['keywords']) for x in items]
	pages= pprint_utils.get_pages(tables, max_len=1950)

	for x in pages: print(f"```py\n{x}\n```")