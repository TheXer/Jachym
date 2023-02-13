from abc import ABC
from typing import Optional

import aiomysql

from src.ui.poll import Poll


class Crud(ABC):
    def __init__(self, poll: aiomysql.pool.Pool):
        self.poll = poll

    async def commit_value(self, sql: str, value: tuple):
        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql, value)
            await conn.commit()

    async def commit_many_values(self, sql: str, values: list[tuple]):
        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.executemany(sql, values)
            await conn.commit()

    async def fetch_all_values(self, sql: str, value: Optional[tuple] = None):
        async with self.poll.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute(sql, value)
            values = await cursor.fetchall()

        return values


class PollDatabase(Crud):
    def __init__(self, database_poll: aiomysql.pool.Pool):
        super().__init__(database_poll)

    async def add(self, discord_poll: Poll):
        sql = "INSERT INTO `Poll`(message_id, channel_id, question, date_created_at, creator_user) " \
              "VALUES (%s, %s, %s, %s, %s)"
        values = (
            discord_poll.message_id,
            discord_poll.channel_id,
            discord_poll.question,
            discord_poll.created_at,
            discord_poll.user_id
        )

        await self.commit_value(sql, values)

    async def remove(self, message_id: int):
        sql = "DELETE FROM `Poll` WHERE message_id = %s"
        value = (message_id,)

        await self.commit_value(sql, value)

    async def fetch_all_polls(self):
        sql = "SELECT * FROM `Poll`"
        polls = await self.fetch_all_values(sql)

        return polls


class VoteButtonDatabase(Crud):
    def __init__(self, pool: aiomysql.pool.Pool):
        super().__init__(pool)

    async def add_options(self, discord_poll: Poll):
        sql = "INSERT INTO `VoteButtons`(message_id, answers) VALUES (%s, %s)"
        values = [
            (discord_poll.message_id, vote_option)
            for vote_option in discord_poll.options
        ]

        await self.commit_many_values(sql, values)

    async def add_user(self, message_id: Poll.message_id, user: int, index: int):
        sql = "INSERT INTO `Answers`(message_id, vote_user, iter_index) VALUES (%s, %s, %s)"
        values = (message_id, user, index)

        await self.commit_value(sql, values)

    async def remove_user(self, message_id: Poll.message_id, user, index):
        sql = "DELETE FROM `Answers` WHERE message_id = %s AND vote_user = %s AND iter_index = %s"
        value = (message_id, user, index)

        await self.commit_value(sql, value)

    async def fetch_all_users(self, message_id: Poll.message_id, index) -> set[int, ...]:
        sql = "SELECT vote_user FROM `Answers` WHERE message_id = %s AND iter_index = %s"
        values = (message_id, index)

        users_voted_for = await self.fetch_all_values(sql, values)

        clean_users_voted_for = set(
            user
            for user_tuple in users_voted_for
            for user in user_tuple
        )

        return clean_users_voted_for


class AnswersDatabase(Crud):
    def __init__(self, pool: aiomysql.pool.Pool):
        super().__init__(pool)

    async def collect_all_answers(self, message_id) -> tuple[str, ...]:
        sql = "SELECT answers FROM `VoteButtons` WHERE message_id = %s"
        value = (message_id,)

        tuple_of_tuples_db = await self.fetch_all_values(sql, value)

        answers = tuple(
            answer
            for tupl in tuple_of_tuples_db
            for answer in tupl
        )

        return answers
