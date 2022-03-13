import aiomysql


class AioSQL:
    """Async context manager for aiomysql, this produces minimal reproducible results."""

    def __init__(self, bot_pool):

        self.database = bot_pool
        self.connection = None
        self.cursor = None

    async def __aenter__(self):
        self.connection = await self.database.acquire()
        self.cursor = await self.connection.cursor()

        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        try:
            await self.cursor.close()

        except aiomysql.Error:
            # TODO: use logging
            # TODO: test connection closing
            self.database.rollback()
            return True

    async def query(self, query: str, val=None):
        await self.cursor.execute(query, val or ())

        return await self.cursor.fetchall()

    async def execute(self, query: str, val=None, commit=True):
        await self.cursor.execute(query, val or ())

        if commit:
            await self.connection.commit()
