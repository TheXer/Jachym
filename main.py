import asyncio
import os

from dotenv import load_dotenv

from src.jachym import Jachym

load_dotenv("password.env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


async def main():
    bot = Jachym()
    async with bot:
        await bot.load_extensions()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
