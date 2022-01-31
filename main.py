import os

import discord
# from discord import activity
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv("password.env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Co jsou intents? https://discordpy.readthedocs.io/en/stable/intents.html
intents = discord.Intents.all()

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=discord.Intents.all(),
    help_command=None,
)

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"{filename[:-3]} has loaded successfully")

        except Exception as error:
            raise error

bot.run(DISCORD_TOKEN)
