from utils.scraper_utils import get_html, get_session
from bs4 import BeautifulSoup
import aiohttp, json, utils, asyncio, re

"""
For pulling the equip-stat ranges from https://reasoningtheory.net/viewranges \
as well as the raw stat values from .../equip/{ID}/(KEY) links
"""

class EquipScraper:
	DATA_LINK= "https://reasoningtheory.net/viewranges"
	LOGIN_FAIL_STRING= "You must be logged on to visit the HentaiVerse."

	# get equip ranges and save as json
	@classmethod
	async def scrape_ranges(cls):
		with aiohttp.ClientSession() as session:
			html= await get_html(cls.DATA_LINK, session)
			data= json.loads(html)
			utils.dump_json(data, utils.RANGES_FILE)
			return data

	@staticmethod
	async def do_hv_login(session=None):
		CONFIG= utils.load_json_with_default(utils.BOT_CONFIG_FILE,default=False)
		if session is None:
			session= get_session()
		session.get(CONFIG['hv_login_link'])
		return session

	@classmethod
	async def scrape_equip(cls, link, session=None, max_tries=3, try_delay=3):
		if session is None:
			session= cls.do_hv_login()

		# get equip page
		async with session:
			html= get_html(link, session)

			tries= 1
			while cls.LOGIN_FAIL_STRING in html and tries < max_tries:
				await asyncio.sleep(try_delay)
				html= get_html(link, session)
				tries+= 1
			if cls.LOGIN_FAIL_STRING in html:
				raise Exception(f"Failed to retrieve equip page after {max_tries} tries with delay {try_delay}s: {link}")

		soup= BeautifulSoup(html, 'html.parser')

		# get name and main stats
		name= soup.find(id="showequip").find("div").get_text(" ")
		stats= cls._get_main_stats(soup.find(class_="ex"))

		# get attack damage (weapons)
		adb= soup.find(lambda x: 'class' in x.attrs and x['class'] in [["eq","et"], ["eq","es"]]).findAll(lambda x: "title" in x.attrs, recursive=False)
		if adb: stats['Attack Damage']= float(adb[0]['title'].replace("Base: ", ""))

		# get special stats
		for ep in soup.findAll(class_="ep"):
			cat= ep.find("div").text
			stats[cat]= cls._get_other_stats(ep)

		# get forge upgrades
		forging= cls._get_upgrades(soup.find("span", id="eu"))

		# get iw enchants
		enchants= cls._get_upgrades(soup.find("span", id="ep"))

		# clean up stats and return
		return dict(
			name=name,
			raw_stats=cls._clean_stat_dict(stats),
			forging=forging,
			enchants=enchants
		)


	@staticmethod
	def _get_main_stats(div):
		ret= {}

		stat_divs= div.findAll(lambda x: "title" in x.attrs)
		for d in stat_divs:
			base= float(d['title'].replace("Base: ",""))
			name= d.find("div").text
			ret[name]= base

		return ret

	@staticmethod
	def _get_other_stats(div):
		ret= {}

		stat_divs= div.findAll(lambda x: "title" in x.attrs)
		for d in stat_divs:
			base= float(d['title'].replace("Base: ",""))
			d.span.clear();	name= d.text.replace(" +","")
			ret[name]= base

		return ret

	@staticmethod
	def _get_upgrades(span):
		ret= dict()
		for x in span.find_all("span"):
			tmp= re.search(r"(.*)(?: Lv\.(\d+))?", x.get_text()) # eg "Strength Bonus Lv.17"
			name,level= tmp.groups()

			if level is None: level= 0 # eg "Hollowforged"
			ret[name]=level

		return ret

	@staticmethod
	def _clean_stat_dict(dct):
		ret= {}
		for cat in dct:
			if type(dct[cat]) is not dict:ret[cat]= dct[cat]

			elif cat == "Primary Attributes":
				for stat in dct[cat]:
					ret[f"{stat}"]= dct[cat][stat]

			elif cat == "Damage Mitigations":
				for stat in dct[cat]:
					ret[f"{stat} MIT"]= dct[cat][stat]

			elif cat == "Spell Damage":
				for stat in dct[cat]:
					ret[f"{stat} EDB"]= dct[cat][stat]

			elif cat == "Proficiency":
				for stat in dct[cat]:
					ret[f"{stat} PROF"]= dct[cat][stat]

			else: raise ValueError(f"Unknown stat category [{cat}]")

		return ret