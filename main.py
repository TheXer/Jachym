"""
Moje narozeniny? Jojo, 27. prosince 2020
"""

import asyncio
import os
from typing import Optional

import aiomysql.pool
import discord
from aiomysql import create_pool
from discord.ext import commands
from dotenv import load_dotenv

from src.db_folder.databases import PollDatabase, AnswersDatabase
from src.helpers import timeit
from src.ui.poll import Poll
from src.ui.poll_view import PollView

load_dotenv("password.env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
USER = os.getenv("USER_DATABASE")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
DATABASE = os.getenv("DATABASE")


class Potkan_Jachym(commands.Bot):
    def __init__(self):
        # Co jsou intents? https://discordpy.readthedocs.io/en/stable/intents.html
        intents = discord.Intents.all()
        self.pool: Optional[aiomysql.pool.Pool] = None
        self.active_discord_polls: set[Poll] = set()

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None
        )

    @timeit
    async def _fetch_polls(self):
        poll_database = PollDatabase(self.pool)
        answers_database = AnswersDatabase(self.pool)

        pools_in_db = await poll_database.fetch_all_polls()

        for message_id, channel_id, question, date, _ in pools_in_db:
            try:
                channel = self.get_channel(channel_id)
                message = await channel.fetch_message(message_id)
                answer = await answers_database.collect_all_answers(message_id)

            except discord.errors.NotFound:
                await poll_database.remove(message_id)
                print(f"Removed a Pool: {message_id, question}")
                continue

            poll = Poll(
                message_id=message_id,
                channel_id=channel_id,
                question=question,
                options=answer,
                date_created=date
            )

            self.add_view(PollView(poll=poll, embed=message.embeds[0], db_poll=self.pool))
            self.active_discord_polls.add(poll)

    async def set_presence(self):
        activity_name = f"Jsem na {len(self.guilds)} serverech a mám spuštěno {len(self.active_discord_polls)} anket!"
        await self.change_presence(activity=discord.Game(name=activity_name))

    @commands.Cog.listener()
    async def on_ready(self):
        self.pool = await create_pool(
            user=USER,
            password=PASSWORD,
            host=HOST,
            db=DATABASE,
            pool_recycle=30,
            maxsize=20
        )
        await self._fetch_polls()
        await self.set_presence()

        print("ready!")

    async def load_extensions(self):
        for filename in os.listdir("cogs/"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")

                    print(f"{filename[:-3]} has loaded successfully")
                except Exception as error:
                    raise error


async def main():
    bot = Potkan_Jachym()
    async with bot:
        await bot.load_extensions()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
