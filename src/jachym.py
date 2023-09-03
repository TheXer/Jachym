from os import getenv, listdir
from typing import TYPE_CHECKING

import discord
from aiomysql import create_pool
from discord.ext import commands
from discord.ext.commands import ExtensionFailed, ExtensionNotFound
from dotenv import load_dotenv
from loguru import logger

from src.db_folder.databases import PollDatabase
from src.helpers import timeit
from src.ui.poll_view import PollView

if TYPE_CHECKING:
    import aiomysql.pool

    from src.ui.poll import Poll

load_dotenv("password.env")


class Jachym(commands.Bot):
    MY_BIRTHDAY = "27.12.2020"
    OWNER_ID = 337971071485607936

    def __init__(self) -> None:
        # https://discordpy.readthedocs.io/en/stable/intents.html
        self.pool: aiomysql.pool.Pool | None = None
        self.active_discord_polls: set[tuple[Poll, discord.Message]] = set()

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=discord.Intents.all(),
            owner_id=self.OWNER_ID,
        )

    @timeit
    async def _fetch_pools_from_database(self) -> None:
        poll_database = PollDatabase(self.pool)

        async for poll, message in poll_database.fetch_all_polls(self):
            self.add_view(
                PollView(poll=poll, embed=message.embeds[0], db_poll=self.pool),
            )
            self.active_discord_polls.add((poll, message))

        logger.success(f"There are now {len(self.active_discord_polls)} active pools!")

    async def set_presence(self) -> None:
        activity_name = f"Jsem na {len(self.guilds)} serverech a mám spuštěno {len(self.active_discord_polls)} anket!"
        await self.change_presence(activity=discord.Game(name=activity_name))

    async def load_extensions(self) -> None:
        for filename in listdir("cogs/"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    logger.success(f"{filename[:-3]} has loaded successfully")
                except (ExtensionNotFound, ExtensionFailed) as error:
                    logger.error(error)

    async def setup_hook(self) -> None:
        logger.info("Getting setup ready...")

        self.pool = await create_pool(
            user=getenv("USER_DATABASE"),
            password=getenv("PASSWORD"),
            host=getenv("HOST"),
            db=getenv("DATABASE"),
            pool_recycle=30,
            maxsize=20,
        )

        await self._fetch_pools_from_database()

        logger.success("Setup ready!")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.set_presence()
        logger.success("Bot online!")
