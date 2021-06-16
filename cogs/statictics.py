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

    # Prepare the table in database
    @commands.Cog.listener()
    async def on_ready(self):
        sql = """
        CREATE TABLE IF NOT EXISTS `Messages`(
        ID_Row INT NOT NULL AUTO_INCREMENT,
        GuildID VARCHAR(255) NOT NULL,
        User VARCHAR(255) NOT NULL,
        CountMessages INT NOT NULL,
        PRIMARY KEY (ID_Row))
        """
        with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
            db.execute(sql, commit=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # Check if user exists in table. If not, create a new row
        # Not efficient, as it asks database every time user types a new message. Maybe use json for validating?
        with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
            sql = "SELECT User FROM Messages;"

            members = {
                x
                for ID in db.query(sql)
                for x in ID}

            if message.author.id not in members:
                sql = "INSERT INTO Messages (GuildID, User, CountMessages) VALUES (%s, %s, %s)"
                db.execute(sql, val=(message.guild.id, message.author.id, 1))

            else:
                pass


def setup(bot):
    bot.add_cog(Statictics(bot))
