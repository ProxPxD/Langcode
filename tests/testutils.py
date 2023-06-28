def remove_alnum(from_str):
	return ''.join(filter(str.isalnum, from_str))


def sort_result(by: int = None, by_length=False):
	def true_decorator(func):
		def inner(*args, **kwargs):
			if by is not None:
				return sorted(func(*args, **kwargs), key=lambda res: len(res[by]) if by_length else res[by])
			return func(*args, **kwargs)
		return inner
	return true_decorator