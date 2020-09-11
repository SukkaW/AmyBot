from utils.error_utils import TemplatedError
import datetime

async def get_html(link, session):
	async with session.get(link) as resp:
		if not resp.status == 200:
			raise TemplatedError("bad_response", link=link, response=resp)
		else:
			return await resp.text(encoding='utf-8')

def to_epoch(year, month, day, hour=0, minute=0):
	args= [int(x) for x in [year,month,day,hour,minute]]
	if args[0] == 20: args[0]= 2000
	return datetime.datetime(*args).timestamp()