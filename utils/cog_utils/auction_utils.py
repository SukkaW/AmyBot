import utils.cog_utils as cmd
from utils.pprint_utils import Column, pprint
from utils.misc_utils import contains
from utils.error_utils import GenericError
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
def _find_equips(name, keywords=None):
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

	if not ret: raise GenericError("no_equip_match", name=name, keywords=keywords)
	return ret


# @ todo: what if multiple base_keys point to same eq_data key
# convert equip results to a table (string) to print
# certain columns are only printed if a relevant keyword is passed in (see key_maps)
def to_table(cmd, eq_name, eq_list, keywords, default_col_name="default_cols"):
	# inits
	CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)
	eq_list.sort(reverse=True, key=lambda x: int(x['price']))

	header_dict= CONFIG[cmd]['headers']
	default_cols= CONFIG[cmd][default_col_name]
	special_cols= ['thread', 'link', 'year'] # these have to be added last for formatting reasons
	key_maps= CONFIG['key_maps']

	has_link= ("link" in keywords and keywords['link']) or "link" in default_cols
	has_thread= ("thread" in keywords and keywords['thread']) or "thread" in default_cols
	has_date= ("year" in keywords or "date" in default_cols) # year is trigger for keywords but date is key for eq_data


	# @TODO: handle key-errors
	# get data for cols to print
	cols= default_cols + [CONFIG['key_maps'][x] for x in keywords if x in CONFIG['key_maps']]
	for x,y in default_cols:
		if x in special_cols: continue # these are handled later

		# create col
		data= [eq[x] for eq in eq_list]
		c= Column(data=data, header=header_dict[x])

		# special formatting
		if x == "stats":
			c.max_width= CONFIG['stat_col_width']
		if x == "price":
			c.data= [str(cmd.int_to_price(x)) for x in c.data]

		cols.append(c)

	# add date col
	if has_date:
		data= []
		for x in eq_list:
			data.append(f"#{x['type'][0].upper()}{x['auction_number']} / {x['date'][1]}-{x['date'][2]}")
		cols.append(Column(data=data, header=header_dict['year']))

	# add link col
	if has_link:
		cols.append(Column(data=[x['link'] for x in eq_list], header=header_dict['link'], is_link=True))

	# add thread col
	# @TODO

	if has_link or has_thread:
		return pprint(columns=cols, prefix=f"**{eq_name}**", code="") # add single ticks
	else:
		return pprint(columns=cols, prefix=f"@ {eq_name}", code=None) # we'll add code-blocks later


if __name__ == "__main__":
	from utils import pprint_utils, parse_utils
	from cogs import auction_cog

	query= "peerl surtr 2019 link"
	parsed= parse_utils.parse_keywords(query,
									   keywords=auction_cog.base_keys,
									   aliases=auction_cog.base_aliases,
									   reps=auction_cog.base_reps)

	items= _find_equips(parsed['clean_query'], parsed['keywords'])
	tables= [to_table("auction", x, items[x], keywords=parsed['keywords']) for x in items]
	pages= pprint_utils.get_pages(tables, max_len=1950)

	for x in pages: print(f"```py\n{x}\n```")