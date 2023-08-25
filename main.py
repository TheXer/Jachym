import asyncio
from os import getenv

import discord.utils
from dotenv import load_dotenv

from src.jachym import Jachym

load_dotenv("password.env")


async def main() -> None:
    bot = Jachym()
    async with bot:
        discord.utils.setup_logging()
        await bot.load_extensions()
        await bot.start(getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
