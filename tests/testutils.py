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


def reapply(fn, arg, n=None, until=None, as_long=None):
	if sum([arg is None for arg in (n, until, as_long)]) < 2:
		raise ValueError
	cond = (lambda a: n > 0) if n is not None else (lambda a: not until(a)) if until is not None else as_long if as_long is not None else (lambda a: False)
	while cond(arg):
		arg = fn(arg)
	return arg

to_last_list = lambda elem: reapply(lambda c: c[0], elem, as_long=lambda c: isinstance(c, list) and len(c) == 1 and isinstance(c[0], list))