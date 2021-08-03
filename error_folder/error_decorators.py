import datetime
import functools
import logging


def log_errors(func):
    """
    A simple logging decorator just for database. For some reason database doesn't work at times, catching the errors
    and logging them to the file to see where is the problem. Thanks to this I can produce more robust code against all
    kinds of errors there is.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.basicConfig(filename=f"{str(datetime.date.today())}.log", level=logging.DEBUG)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = f" Function '{func.__name__}' at {datetime.datetime.now().strftime('%H:%M')} occured an error: {e}\n"
            logging.error(error_message)
            return e

    return wrapper
