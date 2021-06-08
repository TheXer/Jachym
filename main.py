import os
from discord.ext import commands
from dotenv import load_dotenv

import discord

load_dotenv("password.env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Co jsou intents? https://discordpy.readthedocs.io/en/stable/intents.html
intents = discord.Intents.all()

bot = commands.AutoShardedBot(command_prefix="!", intents=intents)
bot.remove_command('help')

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"{filename[:-3]} has loaded successfully")

        except Exception as e:
            print(f"{filename[:-3]} load extension error: {e}")

bot.run(DISCORD_TOKEN)
