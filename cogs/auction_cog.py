from utils.parse_utils import Keyword, KeywordList, to_pos_int, to_bool, parse_keywords
from utils.pprint_utils import pprint, get_pages
from utils.cog_utils import PartialCommand, send_pages, auction_utils as Auct
from discord.ext import commands
import utils, copy


# Keyword stuff
base_keys= KeywordList([
	Keyword("min", to_pos_int),
	Keyword("max", to_pos_int),
	Keyword("date", to_pos_int, aliases=["year", "20", "year20"]),

	Keyword("name", aliases=["name"]),
	Keyword("seller", aliases=["sell"]),
	Keyword("buyer", aliases=["buy"]),

	Keyword("link", to_bool),
	Keyword("thread", to_bool),
	Keyword("rare", to_bool),
	Keyword("norare", to_bool),
])

class AuctionCog(commands.Cog, name="Auction"):
	@commands.command(name="auction", short="auc", cls=PartialCommand)
	async def equip_search(self, ctx):
		equips,keywords= self._search_and_categorize(ctx.query, "name")
		CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)['auction']

		# get tables
		tables= [] # strings
		del keywords['name']
		for eq_name in equips:
			tbl= Auct.to_table("auction", eq_list=equips[eq_name], keyword_list=keywords)
			tbl.eq_name= eq_name
			tables.append(tbl)

		# convert tables to strings
		has_link= keywords['link'] or keywords['thread'] \
				  or 'thread' in CONFIG['default_cols'] or 'link' in CONFIG['default_cols']
		if has_link:
			table_strings= [pprint(x, prefix=f"**{x.eq_name}**", code="") for x in tables] # add single ticks
		else:
			table_strings= [pprint(x, prefix=f"@ {x.eq_name}", code=None) for x in tables] # we'll add code-blocks later

		# group strings into pages
		pages= get_pages(table_strings, max_len=1900)

		# send pages
		await send_pages(ctx, pages, has_link=has_link, code="py" if not has_link else None,
						 page_limit_dm=CONFIG['page_limit_dm'],
						 page_limit_server=CONFIG['page_limit_server'])


	async def transaction(self, ctx, type_):
		assert type_ in ['bought', 'sold'], "Typo in transaction type"

		# inits
		key_name= None
		CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)
		if type_ == "bought": key_name= "buyer"
		elif type_ == "sold": key_name= "seller"

		# get users auction history
		equips,keywords= self._search_and_categorize(ctx.query, key_name)
		equips= list(equips.values())[0]

		# get equip table
		del keywords[CONFIG['key_map'][key_name]]
		eq_table= Auct.to_table(type_, eq_list=equips, keyword_list=keywords)


		# convert tables to strings
		has_link= keywords['link'] or keywords['thread'] \
				  or 'thread' in CONFIG[type_]['default_cols'] or 'link' in CONFIG[type_]['default_cols']
		if has_link:
			# add single ticks
			table_string= pprint(eq_table, code="")
		else:
			# we'll add code-blocks later
			table_string= pprint(eq_table, code=None)

		# group strings into pages
		pages= get_pages(table_string, max_len=1900)

		# send pages
		await send_pages(ctx, pages, has_link=has_link, code="py" if not has_link else None,
			  		     page_limit_dm=CONFIG[type_]['page_limit_dm'],
					     page_limit_server=CONFIG[type_]['page_limit_server'])


	def _search_and_categorize(self, query, key_name):
		# get search parameters
		clean_query,keywords= parse_keywords(query=query, keywords=copy.deepcopy(base_keys))
		keywords[key_name].value= clean_query

		# search equips
		eq_list= Auct.find_equips(keywords)

		# categorize
		dct= {}
		for x in eq_list:
			if x[key_name] not in dct:
				dct[x[key_name]]= []
			dct[x[key_name]].append(x)

		return dct,keywords


	@commands.command(name="bought", short="bou", cls=PartialCommand)
	async def bought(self, ctx): return await self.transaction(ctx, "bought")

	@commands.command(name="sold", short="sol", cls=PartialCommand)
	async def sold(self, ctx): return await self.transaction(ctx, "sold")