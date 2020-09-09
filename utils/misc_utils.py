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