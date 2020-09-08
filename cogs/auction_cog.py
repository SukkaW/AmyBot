import utils.parse_utils as Parse
from utils.pprint_utils import Column, pprint, break_tables
from utils.cog_utils import auction_utils as Auct
from utils.cog_utils import PartialCommand
from discord.ext import commands
import utils


# Keyword stuff
base_keys= { "min": Parse.to_pos_int, "max": Parse.to_pos_int, "year": Parse.to_pos_int,
			 "sell": None, "buy": None,
			 "link": Parse.to_bool, "thread": Parse.to_bool, "rare": Parse.to_bool, "norare": Parse.to_bool
			 }
base_aliases= {"year":["date"]} # alternative keyword names
base_reps= {"year20":["20"]} # replace value with key (before checking names / aliases)

class AuctionCog(commands.Cog, name="Auction"):

	@commands.command(name="auction", short="auc", cls=PartialCommand)
	async def equip_search(self, ctx):
		# get keywords
		parsed= await Parse.handle_keywords(ctx=ctx, keys=base_keys, aliases=base_aliases, reps=base_reps)
		if not parsed: return # Unexpected error in keyword parsing (that's been handled)

		keywords= parsed['keywords']
		clean_query= parsed['clean_query']

		has_link_col= ("link" in keywords and keywords['link']) or ("thread" in keywords and keywords['thread'])

		# get sales table for each matching item
		items= Auct.find_items(clean_query, keywords)
		if not items:
			return await Parse.handle_general_error(ctx, "no_equip_match", name=clean_query, keywords=keywords)

		# convert table to string
		tables= [] # strings
		for eq_name in items:
			tables.append(Auct.to_table(eq_name, items[eq_name], keywords=keywords))

		# merge tables
		CONFIG= utils.load_yaml(utils.PPRINT_CONFIG)['auction']
		pages= break_tables(tables, max_len=1900)
		if not has_link_col:
			pages= [f"```py\n{x}\n```" for x in pages]

		# send results
		if len(pages) > CONFIG['page_limit'] and True:
			omitted= len(pages) - CONFIG['page_limit']

			# @ TODO: template
			nl= '\n' if has_link_col else ''
			pg= 'page' if omitted == 1 else 'pages'
			pages[CONFIG['page_limit']-1]+= f"{nl}{omitted} {pg} omitted. Please DM for the full print-out."
		for x in pages[:CONFIG['page_limit']]:
			await ctx.send(x)