import aiomysql

from poll_design.poll import Poll


# TODO: Reformat it, redundant code all over here!!!

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

    async def add_options(self, discord_poll: Poll):
        sql = """
            INSERT INTO `VoteButtons`(message_id, answers) VALUES (%s, %s)
        """
        values = [
            (discord_poll.message_id, vote_option)
            for vote_option in discord_poll.options
        ]

        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.executemany(sql, values)
            await conn.commit()

    async def add_user(self, message_id, user, index):
        sql = """
            INSERT INTO `Answers`(message_id, vote_user, iter_index) VALUES (%s, %s, %s)
        """
        values = (message_id, user, index)

        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql, values)
            await conn.commit()

    async def remove_user(self, message_id, user, index):
        sql = "DELETE FROM `Answers` WHERE message_id = %s AND vote_user = %s AND iter_index = %s"
        value = (message_id, user, index)

        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql, value)
            await conn.commit()

    async def fetch_all_users(self, message_id, index) -> set:
        sql = """
            SELECT vote_user FROM `Answers` WHERE message_id = %s AND iter_index = %s
        """
        values = (message_id, index)

        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql, values)
            users_voted_for = await cursor.fetchall()

        clean_users_voted_for = set(
            user
            for user_tuple in users_voted_for
            for user in user_tuple
        )

        return clean_users_voted_for

    async def toggle_vote(self, message_id, user, index):
        users = await self.fetch_all_users(message_id, index)

        if user not in users:
            await self.add_user(message_id, user, index)
        else:
            await self.remove_user(message_id, user, index)


class AnswersDatabase(Crud):
    def __init__(self, pool: aiomysql.pool.Pool):
        super().__init__(pool)

    async def collect_all_answers(self, message_id):
        sql = """
            SELECT answers FROM `VoteButtons` WHERE message_id = %s
        """
        value = (message_id,)

        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql, value)
            tuple_of_tuples_db = await cursor.fetchall()

        answers = tuple(
            answer
            for tupl in tuple_of_tuples_db
            for answer in tupl
        )

        return answers
