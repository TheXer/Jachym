"""
Moje narozeniny? Jojo, 27. prosince 2020
"""
import asyncio
import os

import discord
from aiomysql import create_pool
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv("password.env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
USER = os.getenv("USER_DATABASE")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
DATABASE = os.getenv("DATABASE")

# Co jsou intents? https://discordpy.readthedocs.io/en/stable/intents.html
intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    help_command=None)


async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")

                print(f"{filename[:-3]} has loaded successfully")
            except Exception as error:
                raise error


async def main():
    bot.pool = await create_pool(user=USER, password=PASSWORD, host=HOST, db=DATABASE)
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)


@bot.event
async def on_ready():
    guild = discord.Object(id=765657737001828393)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=discord.Object(id=765657737001828393))
    print("ready!")


asyncio.run(main())
