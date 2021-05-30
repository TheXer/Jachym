import datetime
from os import getenv

import discord
import mysql.connector.errors
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv("password.env")

USER = getenv("USER")
PASSWORD = getenv("PASSWORD")
HOST = getenv("HOST")
DATABASE = getenv("DATABASE")


# TODO: UDĚLAT MALÝ WRAPPER PRO DATABÁZI


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = mysql.connector.connect(user=USER, password=PASSWORD, host=HOST, database=DATABASE)
        self.cursor = self.database.cursor()

        self.cache.start()
        self.caching = set()

    def connect(self, **kwargs):
        try:
            self.database = mysql.connector.connect(**kwargs)
            self.cursor = self.database.cursor()
            return self.cursor
        except (AttributeError,
                mysql.connector.errors.OperationalError,
                mysql.connector.errors.ProgrammingError):

            self.database = mysql.connector.connect(**kwargs)
            cursor = self.database.cursor()
            return cursor

    def query(self, query, var=None):
        try:
            self.cursor.execute(query, var or None)
            return self.cursor.fetchall()

        except (AttributeError,
                mysql.connector.errors.OperationalError,
                mysql.connector.errors.ProgrammingError):

            self.cursor = self.connect(user=USER, password=PASSWORD,
                                       host=HOST, database=DATABASE)
            self.cursor.execute(query, var or None)
            return self.cursor.fetchall()

    def close(self, commit=False):
        if commit:
            self.database.commit()
        self.cursor.close()
        self.database.close()

    # RawReaction pro pool systém, automaticky rozpozná jestli někdo reaguje a dá tak odpovídající reakci na tu anketu
    async def reaction_add_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id in self.caching:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            embed = message.embeds[0]
            reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)

            emoticon_dict = {
                "1️⃣": 0,
                "2️⃣": 1,
                "3️⃣": 2,
                "4️⃣": 3,
                "5️⃣": 4,
                "6️⃣": 5,
                "7️⃣": 6,
                "8️⃣": 7,
                "9️⃣": 8,
                "🔟": 9
            }
            i = emoticon_dict[str(payload.emoji)]

            vypis_hlasu = [user.display_name async for user in reaction.users() if not user.id == self.bot.user.id]

            edit = embed.set_field_at(
                i,
                name=embed.fields[i].name,
                value=f"**{len(vypis_hlasu)}** | {', '.join(vypis_hlasu)}",
                inline=False)
            await reaction.message.edit(embed=edit)

    @commands.command()
    async def anketa(self, ctx, question, *answer: str):
        await ctx.message.delete()

        if len(answer) > 10:
            await ctx.send("Zadal jsi příliš mnoho odpovědí, maximum je 10!")

        elif len(answer) == 0 or len(answer) == 1:
            await ctx.send("Nezadal jsi žádnou odpověď nebo příliš málo odpovědí, musíš mít minimálně dvě!")

        elif len(answer) <= 10:
            embed = discord.Embed(
                title="📊 " + question,
                timestamp=ctx.message.created_at,
                color=0xff0000)
            embed.set_footer(text=f"Anketu vytvořil {ctx.message.author.display_name}")

            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

            for x, option in enumerate(answer):
                embed.add_field(
                    name=f"{reactions[x]} {option}",
                    value="**0** |",
                    inline=False)

            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

            sent = await ctx.send(embed=embed)

            for reaction in reactions[:len(answer)]:
                await sent.add_reaction(reaction)

            try:
                self.cursor = self.connect(user=USER, password=PASSWORD, host=HOST, database=DATABASE)
                sql = "INSERT INTO `Poll`(PollID, DateOfPoll) VALUES (%s, %s)"
                val = (sent.id, datetime.datetime.now())

                self.cursor.execute(sql, val)
                self.caching.add(sent.id)

            except mysql.connector.Error as e:
                await ctx.send(e)
                self.database.rollback()

            finally:
                self.close(commit=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_add_remove(payload=payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.reaction_add_remove(payload=payload)

    # Caching systém pro databázi, ať discord bot nebombarduje furt databázi a vše udržuje ve své paměti
    @tasks.loop(minutes=30)
    async def cache(self):
        try:
            self.cursor = self.connect(user=USER, password=PASSWORD, host=HOST, database=DATABASE)

            # Query pro to, aby se každý záznam, který je starší než sedm dní, smazal
            query2 = "DELETE FROM `Poll` WHERE `DateOfPoll` < CURRENT_DATE - 7;"
            self.cursor.execute(operation=query2)

            query = "SELECT `PollID` FROM `Poll`"
            tuples = self.query(query=query)

            # ořezání všeho co tam je, předtím to bylo ve tvaru [('987234', ''..)]
            self.caching = {
                int(clean_variable)
                for variable in tuples
                for clean_variable in variable}

            return self.caching

        except mysql.connector.Error as e:
            print(e)
            self.database.rollback()

        finally:
            self.close(commit=True)

    @cache.before_loop
    async def before_cache(self):
        try:
            self.cursor = self.connect(user=USER, password=PASSWORD, host=HOST, database=DATABASE)
            query = """
			CREATE TABLE IF NOT EXISTS `Poll` (
				ID_Row INT NOT NULL AUTO_INCREMENT,
				PollID VARCHAR(255) NOT NULL,
				DateOfPoll DATE NOT NULL,
				PRIMARY KEY (ID_Row))
			"""
            self.cursor.execute(query)
            print("Table Poll OK")

        except mysql.connector.Error as e:
            print(e)
            self.database.rollback()
            return

        finally:
            self.close(commit=True)

        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Poll(bot))
