import aiomysql

from poll_design.poll import Poll


class Crud:
    def __init__(self, poll: aiomysql.pool.Pool):
        self.poll = poll


class PollDatabase(Crud):
    def __init__(self, database_poll: aiomysql.pool.Pool):
        super().__init__(database_poll)

    async def add(self, discord_poll: Poll):
        sql = """
        INSERT INTO `Poll`(message_id, channel_id, question, date_created_at, creator_user) 
        VALUES (%s, %s, %s, %s, %s)"""
        values = (
            discord_poll.message_id,
            discord_poll.channel_id,
            discord_poll.question,
            discord_poll.date_created_at,
            discord_poll.user_id
        )

        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql, values)
            await conn.commit()

    async def remove(self, discord_poll: Poll):
        sql = """
        DELETE FROM `Poll` WHERE message_id = %s;
        """
        value = discord_poll.message_id

        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql, value)
            await conn.commit()

    async def fetch_all_polls(self):
        sql = """SELECT * FROM `Poll`"""

        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql)
            polls = await cursor.fetchall()

        return polls


class VoteButtonDatabase(Crud):
    def __init__(self, pool: aiomysql.pool.Pool):
        super().__init__(pool)
