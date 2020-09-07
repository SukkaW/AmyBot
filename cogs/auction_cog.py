import utils.command_utils as cmd
from discord.ext import commands
from utils import misc_utils


# Keyword stuff
base_keys= {"date":None, "rare":None, "norare":None, "min":cmd.to_pos_int, "max":cmd.to_pos_int, "user":None, "seller":None, "buyer":None, "debug":None}
base_aliases= {"date":["year"]}
base_reps= {"date20":["20"]}

class AuctionCog(commands.Cog, name="Auction"):
	@commands.command(name="auction", short="auc", cls=cmd.PartialCommand)
	async def equip_search(self, ctx):
		try: tmp= cmd.parse_keywords(ctx.query, base_keys, aliases=base_aliases, reps=base_reps)
		except cmd.ParseError as e:
			usage= misc_utils.get_usage(ctx, e)
			return await ctx.send(f"{usage}")
		except Exception as e:
			return await ctx.send("What the actual fuck.\n\n" + str(e))

		query= tmp['clean_query']
		keywords= tmp['keywords']