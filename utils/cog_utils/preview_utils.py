from utils.scraper_utils import get_session, get_html
from utils.pprint_utils import get_pages, pprint
from utils.parse_utils import int_to_price, contains

from classes.errors import TemplatedError
from classes import EquipScraper, EquipParser, Column

import utils, bs4, datetime, discord, re, asyncio, statistics

async def parse_equip_match(equip_id, equip_key, session, level=0):
	# inits
	CONFIG= utils.load_yaml(utils.PREVIEW_CONFIG)['equip']
	parser= EquipParser()

	# get stats
	equip_link= f"https://hentaiverse.org/equip/{equip_id}/{equip_key}"
	result= await EquipScraper.scrape_equip(equip_link, session=session)
	percentiles= parser.raw_stat_to_percentile(result['name'], result['base_stats'])

	# get preview
	forge_level= 0
	if result['forging']:
		forge_level= statistics.mode(result['forging'].values())

	if level == 2:
		pass # @todo: super-expanded equip preview
	else:
		if level == 1: # expanded form (no stats omitted)
			pass

		else: # show only mandatory / high stats
			def check(stat_name):
				is_mandatory= False
				for x in CONFIG['mandatory_stats']:
					if contains(result['name'], x):
						is_mandatory= is_mandatory or any(contains(stat_name, y) for y in CONFIG['mandatory_stats'][x])


				if stat_name in ['Interference', 'Burden']:
					is_high= percentiles[stat_name] <= 100-CONFIG['min_percentile']
				else:
					is_high= percentiles[stat_name] >= CONFIG['min_percentile']

				return is_high or is_mandatory

			percentiles= { x:y for x,y in percentiles.items() if check(x) }

		# round
		percentiles= { x:round(y) for x,y in percentiles.items() }

		# table cols
		cols= _get_equip_cols(percentiles, CONFIG)

		# forging
		suffix= ""
		if forge_level > 0:
			suffix= f"# Forge {forge_level}"

		# IW potencies
		tmp= []
		for name,lvl in result['enchants'].items():
			if lvl > 0:
				tmp.append(f"{name} {lvl}")
			else:
				tmp.append(name)

		# concatenate upgrades
		if forge_level > 0 and result['enchants']:
			suffix+= " • "
		suffix+= " • ".join(tmp)

		# other info
		tmp= []
		tmp+= ["Tradeable" if result['tradeable'] else "Soulbound"]
		tmp+= [f"Owned by {result['owner']}"]
		if result['level']: tmp.insert(0, f"Level {result['level']}")

		if suffix: suffix+= "\n"
		suffix+= "# " + " • ".join(tmp)

		# return
		if level == 1:
			preview= pprint(cols, prefix=f"@ {result['name']}\n{suffix}", code=None, borders=True)
		else:
			tmp= [y.strip() for x in cols for y in x.data if y.strip()]
			preview= f"@ {result['name']}\n{suffix}\n{', '.join(tmp)}"

		return preview

def _get_equip_cols(percentiles, CONFIG):
	# categorize
	max_len= max(len(str(percentiles[x])) for x in percentiles)
	cats= { c:[] for c in CONFIG['table_categories'] }
	for stat in percentiles:
		abbrv= CONFIG['abbreviations'][stat] if stat in CONFIG['abbreviations'] else stat

		# add stat to cat if mentioned in that cat, else "other"
		for c in CONFIG['table_categories']:
			if any(contains(stat, x) for x in CONFIG['table_categories'][c]):
				cats[c].append((str(percentiles[stat]), abbrv))
				break
		else:
			cats['other'].append((str(percentiles[stat]), abbrv))

	# convert entries to strings
	for c in cats:
		if not cats[c]: continue
		max_len= max(len(x[0]) for x in cats[c])
		cats[c]= [f"{x[0].rjust(max_len)}% {x[1]}" for x in cats[c]]

	# get table columns
	tmp= []
	for x,y in CONFIG['table_headers'].items():
		if cats[x]:
			tmp.append(dict(data=cats[x], header=y))

	# ensure cols same length
	max_len= max(len(x['data']) for x in tmp)
	for x in tmp:
		x['data']+= [""]*(max_len-len(x['data']))

	cols= [Column(**x) for x in tmp]
	return cols

async def parse_thread_match(thread_id, session):
	# inits
	CONFIG= utils.load_yaml(utils.PREVIEW_CONFIG)

	# get html
	thread_link= "https://forums.e-hentai.org/index.php?showtopic=" + thread_id
	html= await get_html(thread_link, session=session)

	# get title + description
	soup= bs4.BeautifulSoup(html, 'html.parser')
	title= soup.find(class_="maintitle").find("div").get_text()
	desc= ""

	split= title.split(",", maxsplit=1)
	if len(split) > 1:
		title= split[0]
		desc= split[1]

	# get sub-forum name
	forum= soup.find(id="navstrip").find_all("a")[-1].get_text()

	# get everything else
	soup= bs4.BeautifulSoup(html, 'html.parser').find("table", cellspacing="1")
	dct= await _parse_post(soup, session)

	# limit preview length
	body= _clean_body(dct['text'], CONFIG=CONFIG)
	title= _clean_title(title, CONFIG=CONFIG)

	# get preview
	render_params= dict(
		title=title,
		sub_title=desc,
		username=dct['username'],
		user_link=dct['user_link'],
		body=body,
		year=dct['year'], month= dct['month'], day=dct['day'],
		forum=forum
	)

	embed= discord.Embed(
		title= utils.render(CONFIG['thread_title_template'], render_params),
		description= utils.render(CONFIG['thread_body_template'], render_params),
		url=thread_link
	)
	embed.set_thumbnail(url=dct['thumbnail'])

	return embed

async def parse_comment_match(thread_id, post_id, session):
	# inits
	CONFIG= utils.load_yaml(utils.PREVIEW_CONFIG)

	# get html
	thread_link= "https://forums.e-hentai.org/index.php?showtopic=" + thread_id + "&view=findpost&p=" + post_id
	html= await get_html(thread_link, session=session)

	# get title + description
	soup= bs4.BeautifulSoup(html, 'html.parser')
	title= soup.find(class_="maintitle").find("div").get_text()
	desc= ""

	split= title.split(",", maxsplit=1)
	if len(split) > 1:
		title= split[0]
		desc= split[1]

	# get sub-forum name
	forum= soup.find(id="navstrip").find_all("a")[-1].get_text()

	# get everything else
	soup= bs4.BeautifulSoup(html, 'html.parser').find(id=f"post-main-{post_id}").parent.parent
	dct= await _parse_post(soup, session)

	# limit preview length
	body= _clean_body(dct['text'], CONFIG=CONFIG)
	title= _clean_title(title, CONFIG=CONFIG)

	# get preview
	render_params= dict(
		title=title,
		username=dct['username'],
		user_link=dct['user_link'],
		body=body,
		year=dct['year'], month= dct['month'], day=dct['day'],
		forum=forum
	)

	embed= discord.Embed(
		title= utils.render(CONFIG['thread_title_template'], render_params),
		description= utils.render(CONFIG['thread_body_template'], render_params),
		url=thread_link
	)
	embed.set_thumbnail(url=dct['thumbnail'])

	return embed

async def parse_bounty_match(bounty_id, session, try_delay=5):
	# inits
	CONFIG= utils.load_yaml(utils.PREVIEW_CONFIG)
	max_tries= CONFIG['max_tries']

	# get html
	bounty_link= "https://e-hentai.org/bounty.php?bid=" + bounty_id
	html= await get_html(bounty_link, session=session)

	tries= 1
	fail_string= "This page requires you to log on."
	while fail_string in html and tries < max_tries:
		await asyncio.sleep(try_delay)
		session= await _do_login(session=session)
		html= await get_html(bounty_link, session)
		tries+= 1
	if fail_string in html:
		print(f"Max retries exceeded for bounty: {bounty_link}")
		return

	# get info
	soup= bs4.BeautifulSoup(html, 'html.parser')

	title= soup.find(class_="stuffbox").find("h1").get_text()
	text= _post_to_text(soup.find(id="x"))
	username= soup.find(class_="r").get_text()
	user_link= soup.find(class_="r").find("a")['href']
	thumbnail= await _get_avatar_link(session, user_link)
	# thumbnail= soup.find("img")['src']

	date= soup.find_all(class_="r")[1].get_text().split()[0]
	year,month,day= [int(x) for x in date.split("-")]

	typ= soup.find_all(class_="r")[2].get_text()
	status= soup.find_all(class_="r")[3].get_text()

	# reward calculations
	tmp= soup.find_all(class_="r")[5].get_text()
	tmp= re.search(r"([\d,]+) Credits \+ ([\d,]+) Hath", tmp).groups()
	credits= int_to_price(tmp[0])
	hath= int_to_price(tmp[1])

	raw_credits= int(tmp[0].replace(",",""))
	raw_hath= int(tmp[1].replace(",",""))

	credit_val= raw_credits + raw_hath*CONFIG['hath_value']
	credit_val= int_to_price(credit_val)

	hath_val= raw_hath + raw_credits // CONFIG['hath_value']
	hath_val= int_to_price(hath_val)

	# limit preview length
	body= _clean_body(text, CONFIG=CONFIG)
	title= _clean_title(title, CONFIG=CONFIG)

	# get preview
	render_params= dict(
		title=title,
		username=username,
		user_link=user_link,
		body=body,
		credits=credits, credit_value=credit_val,
		hath=hath, hath_value=hath_val,
		year=year, month=month, day=day,
		type=typ,
		status=status
	)

	embed= discord.Embed(
		title= utils.render(CONFIG['bounty_title_template'], render_params),
		description= utils.render(CONFIG['bounty_body_template'], render_params),
		url=bounty_link
	)
	embed.set_thumbnail(url=thumbnail)

	return embed

# helper methods --------------

# elem.get_text() wont print correctly due to bbcode formatting
# so apply various fixes before grabbing string to parse
def _post_to_text(soup):
	# [y.replace_with(f"{y.get_text()}") for y in sct.find_all("b")] bold text
	[x.replace_with("\n") for x in soup.find_all("br")] # new lines

	return "\n".join(x for x in soup.get_text().split("\n") if x)

def _get_datetime(time_string):
	MONTHS= "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

	split= time_string.strip().split(" ") # Jul 27 2020, 12:06   OR    Today, 12:58     OR     Yesterday, 23:17
	hr,min= split[-1].split(":") # 12:06

	date= datetime.datetime.today().replace(hour=int(hr),minute=int(min))
	if "Yesterday," in split[0]:
		date= date.replace(day=date.day-1)
	elif "Today," in split[0]:
		pass
	else:
		date= date.replace(year=int(split[2][:-1]), # remove comma
						   month=1+MONTHS.index(split[0]), # month string to 1-indexed int
						   day=int(split[1]))

	return date

async def _parse_post(soup, session):
	# get text content
	post_text= _post_to_text(soup.find(class_="postcolor"))

	# get date
	date= soup.find(lambda x: x.get("style") and "float: left;" in x.get("style") and x.name == "div")
	date= date.get_text().strip()
	date= _get_datetime(date)
	# date= date.strftime("%Y-%m-%d")

	# get user info
	tmp= soup.find("span", class_="bigusername").find("a")
	username= tmp.get_text().strip()
	user_link= tmp['href']

	# get thumbnail link
	thumbnail= await _get_avatar_link(session, user_link)

	return dict(
		text=post_text,
		thumbnail=thumbnail,
		username=username, user_link=user_link,
		year=date.year, month=date.month, day=date.day
	)

async def _get_avatar_link(session, link):
	thumbnail= f"https://forums.e-hentai.org/uploads/av-{link.split('=')[-1]}"
	for x in ['.jpg', '.png']:
		try:
			await get_html(thumbnail+x, session=session)
			thumbnail+= x
			break
		except TemplatedError:
			continue
	else:
		thumbnail=""

	return thumbnail

async def _do_login(session=None):
	CONFIG= utils.load_json_with_default(utils.BOT_CONFIG_FILE,default=False)
	if session is None:
		session= get_session()

	# from chrome's network tab
	headers = {
		'Connection': 'keep-alive',
		'Cache-Control': 'max-age=0',
		'Origin': 'https://e-hentai.org',
		'Upgrade-Insecure-Requests': '1',
		'DNT': '1',
		'Content-Type': 'application/x-www-form-urlencoded',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
		'Sec-Fetch-Site': 'same-site',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-User': '?1',
		'Sec-Fetch-Dest': 'document',
		'Referer': 'https://e-hentai.org/',
		'Accept-Language': 'en-US,en;q=0.9',
	}

	params = (
		('act', 'Login'),
		('CODE', '01'),
	)

	data = {
	  'CookieDate': '1',
	  'b': 'd',
	  'bt': '1-5',
	  'UserName': CONFIG['eh_username'],
	  'PassWord': CONFIG['eh_password'],
	  'ipb_login_submit': 'Login!'
	}

	await session.post(r"https://forums.e-hentai.org/index.php", headers=headers, params=params, data=data)
	return session

def _clean_title(title, CONFIG=None):
	if CONFIG is None:
		CONFIG= utils.load_yaml(utils.PREVIEW_CONFIG)

	if len(title) > CONFIG['max_title_length']:
		title= title[:CONFIG['max_title_length']-3] + "..."
	title= title.replace("\n"," ")
	return title

def _clean_body(body, CONFIG=None):
	if CONFIG is None:
		CONFIG= utils.load_yaml(utils.PREVIEW_CONFIG)

	# limit preview length
	tmp= [x.strip() for x in body.split("\n")]
	pages= get_pages(tmp, max_len=CONFIG['max_body_length'], no_orphan=0, join_char="\n\n")
	body= pages[0]

	split= body.split("\n")
	body= "\n".join(split[:CONFIG['max_body_lines']])
	if len(pages) > 1 or len(split) > CONFIG['max_body_lines']:
		body+= "\n\n[...]"

	# clean up
	while "\n\n\n" in body:
		body= body.replace("\n\n\n","\n\n")

	return body