from utils.error_utils import TemplatedError

async def get_html(link, session):
	async with session.get(link) as resp:
		if not resp.status == 200:
			raise TemplatedError("bad_response", link=link, response=resp)
		else:
			return await resp.text()