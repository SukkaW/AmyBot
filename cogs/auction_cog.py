from utils.parse_utils import Keyword, KeywordList, to_pos_int, to_bool, parse_keywords
from utils.pprint_utils import pprint, get_pages
from utils.cog_utils import PartialCommand, pageify_and_send, check_for_link, stringify_tables
import utils.cog_utils.auction_utils as Auct
from discord.ext import commands
import utils, copy

COG_NAMES= utils.load_yaml(utils.NAME_STRING_FILE)['auction']

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

class AuctionCog(commands.Cog, name=COG_NAMES['cog_name']):

	@commands.command(**COG_NAMES['commands']['auction'], cls=PartialCommand)
	async def equip_search(self, ctx):
		tmp= self._search_and_categorize(ctx.query, "name")
		equips, keywords= tmp['cats'], tmp['keywords']
		CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)['auction']

		# get tables
		tables= [] # strings
		del keywords['name']
		for eq_name in equips:
			tbl= Auct.to_table("auction", eq_list=equips[eq_name], keyword_list=keywords)
			tbl.eq_name= eq_name
			tables.append(tbl)

		# convert tables to strings
		has_link= check_for_link(keywords, CONFIG)
		table_strings= stringify_tables(tables=tables, has_link=has_link, header_func=lambda x: x.eq_name)

		# group into pages and send
		return await pageify_and_send(ctx, strings=table_strings, CONFIG=CONFIG, has_link=has_link)


	async def transaction(self, ctx, type_):
		assert type_ in ['bought', 'sold'], "Typo in transaction type"

		# inits
		key_name= None
		CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)[type_]
		if type_ == "bought": key_name= "buyer"
		elif type_ == "sold": key_name= "seller"

		# get users auction history
		# _search_and_categorize returns multiple results -- if no exact match for username, pick any result
		tmp= self._search_and_categorize(ctx.query, key_name)
		keywords= tmp['keywords']
		for x in tmp['cats']:
			if x.lower() == keywords[key_name].value.lower():
				user, equips= x, tmp['cats'][x]
				break
		else: user, equips= list(tmp['cats'].items())[0]

		# get tables
		del keywords[key_name] # the seller / buyer will be the same for this entire table so don't need col for it
		eq_table= Auct.to_table(type_, eq_list=equips, keyword_list=keywords)
		summary_table= Auct.get_summary_table(equips)

		# convert tables to strings
		has_link= check_for_link(keywords, CONFIG)
		table_strings= []

		table_strings+= stringify_tables(tables=[summary_table], has_link=has_link, header_func=lambda _: f"{user}\n")
		table_strings+= ["\n"] + stringify_tables(tables=[eq_table], has_link=has_link)

		# group into pages and send
		return await pageify_and_send(ctx, strings=table_strings, CONFIG=CONFIG, has_link=has_link)


	def _search_and_categorize(self, query, key_name):
		# get search parameters
		clean_query,keywords= parse_keywords(query=query, keywords=copy.deepcopy(base_keys))
		keywords[key_name].value= clean_query

		# search equips
		eq_list= Auct.find_equips(keywords)

		# categorize
		cats= {}
		for x in eq_list:
			if x[key_name] not in cats:
				cats[x[key_name]]= []
			cats[x[key_name]].append(x)

		return dict(cats=cats, keywords=keywords, clean_query=clean_query)


	@commands.command(**COG_NAMES['commands']['bought'], cls=PartialCommand)
	async def bought(self, ctx): return await self.transaction(ctx, "bought")

	@commands.command(**COG_NAMES['commands']['sold'], cls=PartialCommand)
	async def sold(self, ctx): return await self.transaction(ctx, "sold")