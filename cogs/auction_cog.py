import utils.parse_utils as Parse
from utils.pprint_utils import Column, pprint, get_pages
from utils.cog_utils import PartialCommand, send_pages, auction_utils as Auct
from utils.error_utils import GenericError
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
	@staticmethod
	def get_equips(query):
		# get keywords
		parsed= await Parse.parse_keywords(query=query, keywords=base_keys, aliases=base_aliases, reps=base_reps)

		# search equips
		return Auct._find_equips(parsed['clean_query'], parsed['keywords'])

	@commands.command(name="auction", short="auc", cls=PartialCommand)
	async def equip_search(self, ctx):
		# search equips
		equips= self.get_equips(ctx.query)

		# convert table to string
		tables= [] # strings
		for eq_name in equips:
			tables.append(Auct.to_table("auction", eq_name, equips[eq_name], keywords=equips))

		# send results
		CONFIG= utils.load_yaml(utils.AUCTION_CONFIG)['auction']
		pages= get_pages(tables, max_len=1900)
		has_link= ("link" in equips and equips['link']) or ("thread" in equips and equips['thread'])
		send_pages(ctx, pages, has_link=has_link, code="py",
				   page_limit_dm=CONFIG['page_limit_dm'], page_limit_server=CONFIG['page_limit_server'])

	@commands.command(name="bought", short="auc", cls=PartialCommand)
	async def bought(self, ctx):
		# search equips
		equips= self.get_equips(ctx.query)

		# tally stats
		types= {
			"1h": ["Axe", "Club", "Rapier", "Shortsword", "Wakizashi"],
			"2h": ["Estoc", "Longsword", "Mace", "Katana"],
			"staff": ["Oak", "Redwood", "Willow", "Katalox"],
			"shield": ["Buckler", "Kite", "Force"],
			"cotton": ["Cotton"],
			"phase": ["Phase"],
			"leather": ["Leather"],
			"shade": ["Shade"],
			"plate": ["Plate"],
			"power": ["Power"],
		}