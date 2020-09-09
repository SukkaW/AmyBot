from discord.ext import commands
import utils

class PartialCommand(commands.Command):
	def __init__(self, func, short, *args, **kwargs):
		self.short= short
		super().__init__(func, *args, **kwargs)

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
		pages[-1]+= omit_string

	# prefix / suffix
	pages[0]= prefix + pages[0]
	pages[-1]= pages[-1] + suffix

	# send
	for x in pages:
		await ctx.send(x)