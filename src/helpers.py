import time
from functools import wraps


def timeit(func: callable):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        print(f"{func.__name__} starting...")
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.2f} seconds")

        return result

    return async_wrapper
