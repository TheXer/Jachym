from discord.ext import commands

from db_folder.mysqlwrapper import MySQLWrapper


# import matplot / pandas
# TODO: Look more into which module is better here

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
        with MySQLWrapper() as db:
            db.execute(sql, commit=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            pass



def setup(bot):
    bot.add_cog(Statictics(bot))
