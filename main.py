import utils, json
from cogs import AuctionCog
from utils.perm_utils import check_perms
from core import AmyBot

BOT_CONFIG= json.load(open(utils.BOT_CONFIG_FILE))

bot= AmyBot(BOT_CONFIG['prefix'], case_insensitive=True)

bot.add_cog(AuctionCog())
bot.add_check(check_perms)

bot.run(BOT_CONFIG['discord_key'])