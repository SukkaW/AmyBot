import utils, json
from cogs import AuctionCog
from utils.perm_utils import check_perms
from bot import AmyBot

# inits
BOT_CONFIG= json.load(open(utils.BOT_CONFIG_FILE))
bot= AmyBot(BOT_CONFIG['prefix'], case_insensitive=True)

# load cogs and checks
bot.add_cog(AuctionCog())
bot.add_check(check_perms)

# run
bot.run(BOT_CONFIG['discord_key'])