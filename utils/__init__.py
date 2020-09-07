from .global_utils import *
import jinja2

ENV= jinja2.environment.Environment(trim_blocks=True, lstrip_blocks=True)
def render(template, dct):
	dct= { x.upper():y for x,y in dct.items() }
	return ENV.from_string(template).render(**dct)