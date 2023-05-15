import asyncio
from os import getenv
from dotenv import load_dotenv
from src.jachym import Jachym

load_dotenv("password.env")


async def main():
    bot = Jachym()
    async with bot:
        await bot.load_extensions()
        await bot.start(getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
