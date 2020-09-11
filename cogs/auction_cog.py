import utils.parse_utils as Parse
from utils.parse_utils import Keyword, parse_keywords
from utils.cog_utils import PartialCommand, PartialCog
import utils.cog_utils as Cgu
import utils.cog_utils.auction_utils as Auct
from discord.ext import commands
import utils, copy

COG_NAMES= utils.load_yaml(utils.NAME_STRING_FILE)['auction']

# Keyword stuff
base_keys= Parse.KeywordList([
	Keyword("min", Parse.to_pos_int),
	Keyword("max", Parse.to_pos_int),
	Parse.get_date_key(),

	Keyword("name", Parse.to_potential_string, aliases=["name"]),
	Keyword("seller", Parse.to_potential_string, aliases=["sell", "sold"]),
	Keyword("buyer", Parse.to_potential_string, aliases=["buy", "bought"]),

	Keyword("link", Parse.to_bool),
	Keyword("thread", Parse.to_bool),
	Keyword("rare", Parse.to_bool),
	Keyword("norare", Parse.to_bool),
])

class AuctionCog(PartialCog, name=COG_NAMES['cog_name']):

	@commands.command(**COG_NAMES['commands']['auction'], cls=PartialCommand)
	async def auction(self, ctx):
		# get search parameters
		clean_query,keywords= parse_keywords(query=ctx.query, keywords=copy.deepcopy(base_keys))
		keywords['name'].value= clean_query

		buy= keywords['buyer']
		sell= keywords['seller']

		# check for buyer and seller keywords while ignoring bools
		# (which signal the appearance of a column, but do not affect filtering)
		has_neither= (not buy.has_value and not sell.has_value) or \
					 (not buy.value and not sell.value)
		has_both= (buy.value and sell.value) and \
				  (buy.value is not True and sell.value is not True)

		# if neither buyer or seller or both, use regular auction search
		if has_neither or has_both:
			return await self.equip_search(ctx)
		else:
			eq_list= Auct.find_equips(keywords)

			cats_b= Cgu.categorize(lst=eq_list, key_name="buyer")
			cats_s= Cgu.categorize(lst=eq_list, key_name="seller")
			only_buyer= (keywords['buyer'].has_value and keywords['buyer'].value != True and keywords['seller'].value == True)
			only_seller= (keywords['seller'].has_value and keywords['seller'].value != True and keywords['buyer'].value == True)

			# if specific buyer or specific seller, use special printout
			if len(cats_b.keys()) == 1 or only_buyer:
				del keywords['buyer']
				return await self.buy_sell_search(ctx, "buyer", user=list(cats_b.keys())[0], equips=eq_list, keywords=keywords)
			elif len(cats_s.keys()) == 1 or only_seller:
				del keywords['seller']
				return await self.buy_sell_search(ctx, "buyer", user=list(cats_s.keys())[0], equips=eq_list, keywords=keywords)
			# else, resort to regular search
			else:
				cats= Cgu.categorize(lst=eq_list, key_name="name")
				return await self.equip_search(ctx, keywords=keywords, cats=cats)


	async def equip_search(self, ctx, keywords=None, cats=None):
		# if not already partially-processed...
		if keywords is None and cats is None:
			tmp= self._search_and_categorize(ctx.query, "name")
			cats, keywords= tmp['cats'], tmp['keywords']
		CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)['auction']

		# get tables
		tables= [] # strings
		del keywords['name'] # dont use as col, will be used as prefix for table
		for eq_name in cats:
			tbl= Auct.to_table("auction", eq_list=cats[eq_name], keyword_list=keywords)
			tbl.eq_name= eq_name
			tables.append(tbl)

		# convert tables to strings
		has_link= Cgu.check_for_key("link", keywords, CONFIG) or Cgu.check_for_key("thread", keywords, CONFIG)
		table_strings= Cgu.stringify_tables(tables=tables, has_link=has_link, header_func=lambda x: x.eq_name)

		# group into pages and send
		return await Cgu.pageify_and_send(ctx, strings=table_strings, CONFIG=CONFIG, has_link=has_link)


	# type should be "buyer" or "seller"
	async def buy_sell_search(self, ctx, type_, user=None, equips=None, keywords=None):
		assert type_ in ['buyer', 'seller'], f'Typo in transaction type ("{type_}")'

		# if not already partially-processed...
		if (user is None) and (equips is None) and (keywords is None):
			# get users auction history
			# _search_and_categorize returns multiple results -- if no exact match for username, pick any result
			tmp= self._search_and_categorize(ctx.query, type_)
			keywords= tmp['keywords']
			for x in tmp['cats']:
				if x.lower() == keywords[type_].value.lower():
					user, equips= x, tmp['cats'][x]
					break
			else: user, equips= list(tmp['cats'].items())[0]

		# get tables
		CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)

		del keywords[type_] # the seller / buyer will be the same for this entire table so don't need col for it
		eq_table= Auct.to_table(type_, eq_list=equips, keyword_list=keywords)
		summary_table= Cgu.misc_utils.get_summary_table(equips, CONFIG)

		# convert tables to strings
		has_link= Cgu.check_for_key("link", keywords, CONFIG[type_] ) or Cgu.check_for_key("thread", keywords, CONFIG[type_] )

		summary_strings= Cgu.stringify_tables(tables=[summary_table], has_link=has_link, header_func=lambda _: f"{user}\n", code="py")
		main_strings= Cgu.stringify_tables(tables=[eq_table], has_link=has_link)
		table_strings= summary_strings + main_strings

		# group into pages and send
		return await Cgu.pageify_and_send(ctx, strings=table_strings, CONFIG=CONFIG[type_], has_link=has_link)


	@staticmethod
	def _search(query=None, key_name=None):
		# get search parameters
		clean_query,keywords= parse_keywords(query=query, keywords=copy.deepcopy(base_keys))
		keywords[key_name].value= clean_query

		# search equips
		eq_list= Auct.find_equips(keywords)

		return dict(eq_list=eq_list, keywords=keywords, clean_query=clean_query)

	@classmethod
	def _search_and_categorize(cls, query, key_name):
		result= cls._search(query=query, key_name=key_name)
		cats= Cgu.categorize(result['eq_list'], key_name)
		return dict(cats=cats, keywords=result['keywords'], clean_query=result['clean_query'])


	@commands.command(**COG_NAMES['commands']['bought'], cls=PartialCommand)
	async def bought(self, ctx):
		clean_query,keyword_list= parse_keywords(query=ctx.query, keywords=copy.deepcopy(base_keys))
		return await ctx.send(f"This command has been moved to `{ctx.prefix}auction`. Instead, please try\n```fix\n{ctx.prefix}auction buy{clean_query.upper()} {keyword_list.to_query()}```")
		# return await self.buy_sell_search(ctx, "buyer")

	@commands.command(**COG_NAMES['commands']['sold'], cls=PartialCommand)
	async def sold(self, ctx):
		clean_query,keyword_list= parse_keywords(query=ctx.query, keywords=copy.deepcopy(base_keys))
		return await ctx.send(f"This command has been moved to `{ctx.prefix}auction`. Instead, please try\n```fix\n{ctx.prefix}auction sell{clean_query.upper()} {keyword_list.to_query()}```")
		# return await self.buy_sell_search(ctx, "seller")