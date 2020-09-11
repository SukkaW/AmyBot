from utils.scraper_utils import get_html
from bs4 import BeautifulSoup
import aiohttp, json, utils

"""
For pulling the equip-stat ranges from https://reasoningtheory.net/viewranges \
as well as the raw stat values from .../equip/{ID}/(KEY) links
"""

class EquipScraper:
	DATA_LINK= "https://reasoningtheory.net/viewranges"

	# get equip ranges and save as json
	@classmethod
	async def scrape_ranges(cls):
		with aiohttp.ClientSession() as session:
			html= await get_html(cls.DATA_LINK, session)
			data= json.loads(html)
			utils.dump_json(data, utils.RANGES_FILE)
			return data

	@classmethod
	async def scrape_raw_stats(cls, link):
		with aiohttp.ClientSession() as session:
			# get page
			html= get_html(link, session)
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

			# clean up stats and return
			return name,cls._clean_stat_dict(stats)


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