import os, json
from ruamel.yaml import YAML

# Checks that all words in to_find are contained in to_search
def contains(to_search, to_find):
	if isinstance(to_find, list):
		pass
	elif isinstance(to_find, str):
		to_find= [x.lower() for x in to_find.split()]
	else: raise ValueError(f"'{type(to_find)}' passed to 'contains' function as 'to_find' arg")

	to_search= to_search.lower()
	return all(x in to_search for x in to_find)

def load_yaml(path):
	return YAML().load(open(path))

def dump_yaml(data, path):
	return YAML().dump(data, open(path, "w"))


# yamls are assumed to be pre-existing because they contain templates, but...
# thats not assumed for jsons to make it easy to manually delete cache and force re-parsing
def load_json_with_default(path, default=None):
	if default is None: default= {}

	# make parent dirs if not exists
	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	# load json, using default if necessary
	if os.path.exists(path):
		return json.load(open(path, encoding='utf-8'))
	elif default is not False:
		json.dump(default, open(path, "w"), indent=2)
		return default
	else:
		raise Exception(f"No default supplied and file does not exist: {path}")


def dump_json(data, path):
	# make parent dirs if not exists
	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	# dont use \u characters
	json.dump(data, open(path,"w",encoding='utf-8'), ensure_ascii=False, indent=2)