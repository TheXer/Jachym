import time
from functools import wraps

from loguru import logger


def timeit(func: callable):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger.info(f"{func.__name__} starting...")
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f'{func.__name__} took {duration:.2f} seconds')
        return result

    return async_wrapper
