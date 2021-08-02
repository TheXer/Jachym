from os import getenv

from discord.ext import commands
from dotenv import load_dotenv

from db_folder.mysqlwrapper import MySQLWrapper

# import matplot / pandas
# TODO: Look more into which module is better here

load_dotenv("password.env")

USER = getenv("USER_DATABASE")
PASSWORD = getenv("PASSWORD")
HOST = getenv("HOST")
DATABASE = getenv("DATABASE")


class Statictics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.caching = set()

    # Prepare the table in database
    @commands.Cog.listener()
    async def on_ready(self):
        sql = """
        CREATE TABLE IF NOT EXISTS `Messages`(
        GuildID VARCHAR(255) NOT NULL,
        User VARCHAR(255) NOT NULL,
        CountMessages INT NOT NULL,
        PRIMARY KEY (User))
        """
        with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
            db.execute(sql, commit=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        elif message.guild.id in self.caching:
            pass

    @commands.group()
    async def stats(self, ctx):
        self.caching.add(ctx.guild.id)

        await ctx.send("OK")


def setup(bot):
    bot.add_cog(Statictics(bot))
