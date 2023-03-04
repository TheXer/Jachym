from os import getenv, listdir
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


class Jachym(commands.Bot):
    MY_BIRTHDAY = "27.12.2020"

    def __init__(self):
        # https://discordpy.readthedocs.io/en/stable/intents.html
        intents = discord.Intents.all()
        self.pool: Optional[aiomysql.pool.Pool] = None
        self.active_discord_polls: set[Poll] = set()

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None
        )

    @timeit
    async def _fetch_pools_from_database(self):
        poll_database = PollDatabase(self.pool)
        answers_database = AnswersDatabase(self.pool)

        pools_in_db = await poll_database.fetch_all_polls()

        for message_id, channel_id, question, date, _ in pools_in_db:
            try:
                message = await self.get_channel(channel_id).fetch_message(message_id)

            except discord.errors.NotFound:
                await poll_database.remove(message_id)
                print(f"Removed a Pool: {message_id, question}")
                continue

            answer = await answers_database.collect_all_answers(message_id)

            poll = Poll(
                message_id=message_id,
                channel_id=channel_id,
                question=question,
                options=answer,
                date_created=date
            )

            self.add_view(PollView(poll=poll, embed=message.embeds[0], db_poll=self.pool))
            self.active_discord_polls.add(poll)

        print(f"There are now {len(self.active_discord_polls)} active pools!")

    async def set_presence(self):
        activity_name = f"Jsem na {len(self.guilds)} serverech a mám spuštěno {len(self.active_discord_polls)} anket!"
        await self.change_presence(activity=discord.Game(name=activity_name))

    @commands.Cog.listener()
    async def on_ready(self):
        self.pool = await create_pool(
            user=getenv("USER_DATABASE"),
            password=getenv("PASSWORD"),
            host=getenv("HOST"),
            db=getenv("DATABASE"),
            pool_recycle=30,
            maxsize=20)

        await self._fetch_pools_from_database()
        await self.set_presence()

        print("Ready!")

    async def load_extensions(self):
        for filename in listdir("cogs/"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")

                    print(f"{filename[:-3]} has loaded successfully")
                except Exception as error:
                    raise error