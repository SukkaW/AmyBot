from discord.ext import tasks

from utils.cog_utils.data_utils import check_update_log, merge_auctions, merge_items
from classes import PartialCog, SuperScraper, MarketScraper, EquipScraper

import utils, os

class UpdateCog(PartialCog):
	def __init__(self):
		super().__init__(hidden=True)
		self.check_market.start()
		self.check_super.start()

	# check super every sunday for equips + items
	@tasks.loop(hours=6)
	async def check_super(self):
		super_check= check_update_log("super", 24*60*60, exact_day=6)

		if super_check:
			print("Checking super...")
			await SuperScraper.scrape()
		if super_check or not os.path.exists(utils.AUCTION_FILE):
			await SuperScraper.parse()
			await merge_auctions()

	# check hvmarket for items
	@tasks.loop(hours=1)
	async def check_market(self):
		CONFIG= utils.load_json_with_default(utils.BOT_CONFIG_FILE, default=False)
		hvm_check= check_update_log("hvmarket", 3600*CONFIG['market_check_frequency_hours'])

		if hvm_check:
			print("Checking market...")
			await MarketScraper.scrape()
		if hvm_check or not os.path.exists(utils.ITEM_FILE):
			await merge_items()

	# update min/max ranges for equip stats
	@tasks.loop(hours=6)
	async def update_ranges(self):
		CONFIG= utils.load_json_with_default(utils.BOT_CONFIG_FILE, default=False)
		range_check= check_update_log("equip_ranges", 24*CONFIG['equip_range_check_frequency_hours'])

		if range_check or not os.path.exists(utils.RANGES_FILE):
			print("Updating equip ranges...")
			await EquipScraper.scrape_ranges()

	# check kedama fo... jk, her auctions discountinued
	# @tasks.loop(hours=12)
	# async def check_kedama(self):
		# kedama_check= check_update_log("kedama", 6.9*24*60*60)
		# if kedama_check:
		# 	await KedamaScraper.scrape()
		# 	KedamaScraper.parse()