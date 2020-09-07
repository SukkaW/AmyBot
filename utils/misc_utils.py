# Checks that all words in to_find are contained in to_search
def contains(to_search, to_find):
	to_search= to_search.lower()
	to_find= [x.lower() for x in to_find.split()]
	return all(x in to_search for x in to_find)