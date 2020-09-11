from discord.ext import commands
import utils.pprint_utils as Pprint
import utils

class PartialCommand(commands.Command):
	def __init__(self, func, short, **kwargs):
		self.short= short
		super().__init__(func, **kwargs)

class PartialCog(commands.Cog):
	def __init__(self, hidden=False, **kwargs):
		self.hidden=hidden
		super().__init__(**kwargs)


async def pageify_and_send(ctx, strings, CONFIG, has_link=False, max_len=1900):
	# group strings into pages
	pages= Pprint.get_pages(strings, max_len=max_len)

	# send pages
	await send_pages(ctx, pages, has_link=has_link, code="py" if not has_link else None,
					 page_limit_dm=CONFIG['page_limit_dm'],
					 page_limit_server=CONFIG['page_limit_server'])

def check_for_link(keywords, CONFIG):
		return keywords['link'] \
			   or keywords['thread'] \
			   or 'thread' in CONFIG['default_cols'] \
			   or 'link' in CONFIG['default_cols']


def stringify_tables(tables, has_link=False, header_func=None):
	# convert tables to strings
	table_strings= []
	for x in tables:
		if has_link:
			prefix= f"**{header_func(x)}**" if header_func is not None else ""
			table_strings.append(Pprint.pprint(x, prefix=prefix, code="")) # add single ticks
		else:
			prefix= f"@ {header_func(x)}" if header_func is not None else ""
			table_strings.append(Pprint.pprint(x, prefix=prefix, code=None)) # we'll add code-blocks later

	return table_strings


# @ todo: check max length (2000)
# send to discord, enforcing a page limit and optionally wrapping in code blocks
async def send_pages(ctx, pages, code=None, page_limit_server=2, page_limit_dm=None, has_link=False, prefix="", suffix=""):
	# code blocks
	if code:
		pages= [f"```{code}\n{x}\n```" for x in pages]

	# append "# pages omitted" warning
	limit= page_limit_server if ctx.guild is not None else page_limit_dm
	if len(pages) > limit:
		STRINGS= utils.load_yaml(utils.PPRINT_STRING_FILE)
		dct= {
			"PAGES": pages,
			"PAGE_LIMIT": limit,
			"HAS_LINK": has_link
		}
		omit_string= utils.render(STRINGS['omit_template'], dct)
		pages[limit-1]+= omit_string

	# prefix / suffix
	pages[0]= prefix + pages[0]
	pages[-1]= pages[-1] + suffix

	# send
	for x in pages[:limit]:
		await ctx.send(x)