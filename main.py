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

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    help_command=None)


@bot.event
async def on_ready():
    bot.pool = await create_pool(user=USER, password=PASSWORD, host=HOST, db=DATABASE)
    print("database running")

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"{filename[:-3]} has loaded successfully")

            except Exception as error:
                raise error


bot.run(DISCORD_TOKEN)
