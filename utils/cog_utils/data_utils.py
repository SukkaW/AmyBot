"""
Functions for loading each main data file, creating the file from cached pages if necessary.
"""

from scrapers import SuperScraper, KedamaScraper, MarketScraper, EquipScraper
from datetime import datetime
import utils, os

async def merge_auctions():
	# get data
	if not os.path.exists(utils.SUPER_EQUIP_FILE):
		_,s_data= await SuperScraper.parse()
	else: s_data= utils.load_json_with_default(utils.SUPER_EQUIP_FILE, default=False)

	if not os.path.exists(utils.KEDAMA_EQUIP_FILE):
		_,k_data= KedamaScraper.parse()
	else: k_data= utils.load_json_with_default(utils.KEDAMA_EQUIP_FILE, default=False)

	# merge data
	merged_data= []
	for x in s_data:
		x['type']= "super"
		merged_data.append(x)
	for x in k_data:
		x['type']= "kedama"
		merged_data.append(x)

	# for visual consistency
	merged_data= [{ y:x[y] for y in ["name","price","level","stats","seller","buyer","type","auction_number","link","thread"] } for x in merged_data]

	# dump
	utils.dump_json(merged_data, utils.AUCTION_FILE)
	return merged_data

async def merge_items():
	# get data
	if not os.path.exists(utils.SUPER_EQUIP_FILE):
		_,s_data= await SuperScraper.parse()
	else: s_data= utils.load_json_with_default(utils.SUPER_ITEM_FILE, default=False)

	if not os.path.exists(utils.KEDAMA_ITEM_FILE):
		_,k_data= KedamaScraper.parse()
	else: k_data= utils.load_json_with_default(utils.KEDAMA_ITEM_FILE, default=False)

	if not os.path.exists(utils.MARKET_ITEM_FILE):
		_,h_data= await MarketScraper.scrape()
	else: h_data= utils.load_json_with_default(utils.SUPER_EQUIP_FILE, default=False)


	# merge data
	merged_data= []
	for x,y in [('super',s_data), ('kedama',k_data), ('hvmarket',h_data)]:
		y['type']= x

	# for visual consistency
	merged_data= [{ y:x[y] for y in ["name","price","level","stats","seller","buyer","type","auction_number","link","thread"] } for x in merged_data]

	# dump
	utils.dump_json(merged_data, utils.ITEM_FILE)
	return merged_data

def check_update_log(check_name, min_time, exact_day=None):
	# inits
	time_check= False
	day_check=False
	log= utils.load_json_with_default(utils.UPDATE_LOG)

	if check_name not in log:
		log[check_name]= 0

	# check if right day
	if datetime.today().weekday() == exact_day or exact_day is None:
		day_check= True

	# check if enough time has passed since last check
	if day_check:
		now= datetime.now().timestamp()
		if now - log[check_name] > min_time:
			time_check= True
			log[check_name]= now

	# dump and return
	utils.dump_json(log, utils.UPDATE_LOG)
	return day_check and time_check
