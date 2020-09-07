from utils.misc_utils import contains
import json, utils

def find_items(name, keywords=None):
	ret= {}
	data= json.load(open(utils.AUCTION_FILE))
	if keywords is None: keywords= {}

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

	for eq_name in data:
		if not contains(to_search=eq_name, to_find=name): continue
		if not all(chk(eq_name) for chk in name_checks): continue

		for eq in data[eq_name]:
			if all(chk(eq) for chk in eq_checks):
				if eq_name not in ret:
					ret[eq_name]= []
				ret[eq_name].append(eq)

	return ret

def is_rare(name):
	rares= ["Slaughter", "Savage", "Mystic", "Shielding", "Charged", "Frugal", "Radiant"]
	return any(x.lower() in name.lower() for x in rares)

if __name__ == "__main__":
	from utils import cog_utils
	from cogs import auction_cog
	from utils import pprint_utils

	query= "peerl surtr 2019"
	try:
		parsed= cog_utils.parse_keywords(query,
										   keywords=auction_cog.base_keys,
										   aliases=auction_cog.base_aliases,
										   reps=auction_cog.base_reps)
	except cog_utils.ParseError as e:
		print(e)
	else:
		items= find_items(parsed['clean_query'], parsed['keywords'])
		tables= [auction_cog._to_table(x, items[x], keywords=parsed['keywords']) for x in items]
		pages= pprint_utils.break_tables(tables, max_len=1950)

		for x in pages: print(f"```py\n{x}\n```")