import utils.cog_utils as cmd
from utils.pprint_utils import Column, pprint, break_tables
from utils.cog_utils import auction_utils as auct
from discord.ext import commands
import utils, yaml


# Keyword stuff
base_keys= { "min": cmd.to_pos_int, "max": cmd.to_pos_int, "year": cmd.to_pos_int,
			 "sell": None, "buy": None,
			 "thread":cmd.to_bool, "rare": cmd.to_bool, "norare": cmd.to_bool
			 }
base_aliases= {"year":["date"]} # alternative keyword names
base_reps= {"year20":["20"]} # replace value with key (before checking names / aliases)

class AuctionCog(commands.Cog, name="Auction"):

	@commands.command(name="auction", short="auc", cls=cmd.PartialCommand)
	async def equip_search(self, ctx):
		parsed= await cmd.handle_keywords(ctx=ctx, keys=base_keys, aliases=base_aliases, reps=base_reps)
		if not parsed: return # Unexpected error in keyword parsing (that's been handled)

		# Get sales table for each matching item
		items= auct.find_items(parsed['clean_query'], parsed['keywords'])
		if not items:
			return await cmd.handle_general_error(ctx, "no_equip_match", name=parsed['clean_query'], keywords=parsed['keywords'])

		# Convert table to string
		tables= [] # strings
		for eq_name in items:
			tables.append(_to_table(eq_name, items[eq_name], keywords=parsed['keywords']))

		# Merge tables
		CONFIG= yaml.safe_load(open(utils.PPRINT_CONFIG))['auction']
		pages= break_tables(tables, max_len=1900)
		pages= [f"```py\n{x}\n```" for x in pages]

		# Send results
		if len(pages) > CONFIG['page_limit']:
			omitted= len(pages) - CONFIG['page_limit']
			pages[-1]+= f"\n{omitted} {'page' if omitted == 1 else 'pages'} omitted."
		for x in pages[:CONFIG['page_limit']]:
			await ctx.send(x)


def _to_table(eq_name, eq_list, keywords):
	CONFIG= yaml.safe_load(open(utils.PPRINT_CONFIG))['auction']
	eq_list.sort(reverse=True, key=lambda x: int(x['price']))

	header_dict= CONFIG['headers']
	default_cols= CONFIG['default_cols']
	keyword_cols= CONFIG['keyword_cols']

	col_names= default_cols + [keyword_cols[x] for x in keyword_cols if x in keywords]

	cols= []
	for x in col_names:
		# @TODO: handle key-errors

		data= [eq[x] for eq in eq_list]
		c= Column(data=data, header=header_dict[x])

		if x == "stats": c.max_width= CONFIG['stat_col_width']
		if x == "price": c.data= [str(cmd.int_to_price(x)) for x in c.data]

		cols.append(c)

	# add dates
	data= []
	for x in eq_list:
		data.append(f"#{x['type'][0].upper()}{x['auction_number']} / {x['date'][1]}-{x['date'][2]}")
	cols.append(Column(data=data, header=header_dict['year']))

	return pprint(columns=cols, prefix=f"@ {eq_name}", code=None)
