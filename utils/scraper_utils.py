from utils.error_utils import TemplatedError
import datetime, aiohttp

async def get_html(link, session):
	async with session.get(link) as resp:
		if not resp.status == 200:
			raise TemplatedError("bad_response", link=link, response=resp)
		else:
			return await resp.text(encoding='utf-8')

def get_session():
	# keep-alive because https://github.com/aio-libs/aiohttp/issues/3904#issuecomment-632661245
	return aiohttp.ClientSession(headers={'Connection': 'keep-alive'})