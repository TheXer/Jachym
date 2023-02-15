import time
from functools import wraps


def timeit(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start

        print(f'{func.__name__} took {round(duration, 1)} seconds')

        return result

    return async_wrapper
