from functools import wraps

def apply(transform):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return transform(result)
        return wrapper
    return decorator