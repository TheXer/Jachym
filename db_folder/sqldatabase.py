from os import getenv

import aiomysql
from dotenv import load_dotenv

load_dotenv("../password.env")

USER = getenv("USER_DATABASE")
PASSWORD = getenv("PASSWORD")
HOST = getenv("HOST")
DATABASE = getenv("DATABASE")


class AioSQL:
    """Async context manager for aiomysql, this produces minimal reproducible results."""

    def __init__(self, **credentials):
        if not credentials:
            self.credentials = {"user": USER, "password": PASSWORD, "host": HOST, "db": DATABASE}
        else:
            self.credentials = credentials
        self.database = None
        self.cursor = None

    async def __aenter__(self):
        self.database = await aiomysql.connect(**self.credentials)
        self.cursor = await self.database.cursor()

        return self.cursor

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        try:
            await self.cursor.close()
            self.database.close()

        except aiomysql.Error:
            # use logging
            self.database.rollback()
            return True
