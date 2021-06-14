import datetime
import json
from os import getenv

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from db_folder.mysqlwrapper import MySQLWrapper

load_dotenv("password.env")

USER = getenv("USER_DATABASE")
PASSWORD = getenv("PASSWORD")
HOST = getenv("HOST")
DATABASE = getenv("DATABASE")


class EventSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.caching = set()

        self.cache.start()
        self.poslanieventu.start()

    # Caching systém, oproti caching systému ve poll.py se tento vždy smaže pokud je event odeslán a zpracován.
    @tasks.loop(minutes=30)
    async def cache(self):
        with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
            query = "SELECT `EventEmbedID` FROM `EventPlanner`"
            tuples = db.query(query=query)

            self.caching = {
                int(clean_variable)
                for variable in tuples
                for clean_variable in variable}

            return self.caching

    @cache.before_loop
    async def before_cache(self):
        await self.bot.wait_until_ready()

    # Ověřuje databázi jestli něco není starší než dané datum a pak jej pošle.
    @tasks.loop(seconds=5.0)
    async def poslanieventu(self):
        with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:

            sql = "SELECT * FROM EventPlanner;"
            result = db.query(query=sql)

            for GuildID, EventID, EventTitle, EventDescription, EventDate, ChannelID in result:
                if datetime.datetime.now() < EventDate:
                    continue

                sql = "SELECT ReactionUser FROM ReactionUsers WHERE EventEmbedID = %s;"
                result = db.query(query=sql, val=(EventID,))

                members = {
                    await self.bot.fetch_user(int(x))
                    for ID in result
                    for x in ID}

                embed = discord.Embed(
                    title=f"**Pořádá se akce:** {EventTitle}",
                    description=f"{EventDescription}",
                    colour=discord.Colour.gold())

                file = discord.File("fotky/trojuhelnik.png", filename="trojuhelnik.png")
                embed.set_thumbnail(url="attachment://trojuhelnik.png")

                if len(members) == 0:
                    embed.add_field(name="Účastníci", value="Nikdo nejede.")

                elif len(members) > 0:
                    embed.add_field(name="Účastníci", value=f"{','.join(user.mention for user in members)}")

                channel = self.bot.get_channel(int(ChannelID))
                await channel.send(file=file, embed=embed)

                sql2 = "DELETE FROM EventPlanner WHERE EventEmbedID = %s;"
                db.execute(sql2, (EventID,), commit=True)

                msg = await channel.fetch_message(EventID)
                await msg.delete()

    @poslanieventu.before_loop
    async def before_poslanieventu(self):
        tables = {
            'EventPlanner': ("""
                    CREATE TABLE IF NOT EXISTS `EventPlanner` (
                    GuildID VARCHAR(255) NOT NULL,
                    EventEmbedID VARCHAR(255) NOT NULL,
                    EventTitle VARCHAR(255) NOT NULL,
                    EventDescription VARCHAR(255) NOT NULL,
                    EventDate DATETIME NOT NULL,
                    ChannelID VARCHAR(255) NOT NULL,
                    PRIMARY KEY (EventEmbedID))
                """),
            'ReactionUsers': ("""
                    CREATE TABLE IF NOT EXISTS `ReactionUsers` (
                        ID_row INT NOT NULL AUTO_INCREMENT,
                        EventEmbedID VARCHAR(255) NOT NULL,
                        ReactionUser VARCHAR(255) NOT NULL,
                        PRIMARY KEY (ID_row),
                        FOREIGN KEY (EventEmbedID) 
                            REFERENCES EventPlanner(EventEmbedID)
                            ON DELETE CASCADE)
                """)}

        for table_name in tables:
            table_description = tables[table_name]

            with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
                db.execute(query=table_description, commit=True)

        await self.bot.wait_until_ready()

    # help systém pro to.
    @commands.group(invoke_without_command=True)
    async def udalost(self, ctx):
        with open("text_json/package.json") as f:
            test = json.load(f)

        embed = discord.Embed.from_dict(test["udalost"])
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @udalost.command()
    async def create(self, ctx, title, description, eventdatetime):
        try:
            datetime_formatted = datetime.datetime.strptime(eventdatetime, '%d.%m.%Y %H:%M')
            if datetime.datetime.now() > datetime_formatted:
                return await ctx.send("Nemůžeš zakládat událost, která se stala v minulosti!")

        except ValueError:
            return await ctx.send(
                "Špatně zformátované datum. Napiš to ve formátu **DD.MM.YYYY HH:MM**, pro příklad **04.01.2021 12:01**")

        if title == "":
            return await ctx.send("`Nemůžeš vytvořit událost beze jména`")

        if description == "":
            return await ctx.send("`Události musíš vytvořit nějaký popis, například co se na ní bude dělat`")

        embed = discord.Embed(title=title, description=description, colour=discord.Colour.gold())
        embed.add_field(name="Datum", value=f"{datetime_formatted:%d.%m.%Y %H:%M}")
        embed.add_field(name="Ano, pojedu:", value="0 |", inline=False)
        embed.add_field(name="Ne, nejedu:", value="0 |", inline=False)
        reactions = ["✅", "❌"]

        sent = await ctx.send(embed=embed)
        for reaction in reactions:
            await sent.add_reaction(reaction)

        sql = """INSERT INTO `EventPlanner` (
                    GuildID,
                    EventEmbedID, 
                    EventTitle,
                    EventDescription,
                    EventDate,
                    ChannelID
                ) VALUES (%s, %s, %s, %s, %s, %s)"""
        val = (ctx.guild.id, sent.id, title, description, datetime_formatted, ctx.channel.id)

        with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
            db.execute(sql, val, commit=True)

        self.caching.add(sent.id)

    @udalost.command()
    async def vypis(self, ctx):
        sql = """
            SELECT EventTitle, EventDescription, EventDate 
            FROM EventPlanner 
            WHERE GuildID = %s
            ORDER BY EventDate; """

        with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
            result = db.query(query=sql, val=(ctx.guild.id,))
            embed = discord.Embed(title="Výpis všech událostí", colour=discord.Colour.gold())

            for title, description, date in result:
                embed.add_field(name=title, value=f"{date: %d.%m.%Y %H:%M} | {description}", inline=False)

        await ctx.send(embed=embed)

    # Smaže event z databáze pomocí ID embedu. Přijít na lepší způsob?
    @udalost.command(aliases=["delete"])
    async def smazat(self, ctx, embed_id: str):
        with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
            try:
                sql = "DELETE FROM EventPlanner WHERE EventEmbedID = %s;"
                db.execute(sql, (embed_id,), commit=True)

                msg = await ctx.fetch_message(embed_id)
                await msg.delete()

                await ctx.send("Úspěšně smazán event")

            except discord.errors.NotFound:
                await ctx.send("Zkontroluj si číslo, páč tento není v mé paměti. Možná jsi to blbě napsal?")

    # To stejné, akorát s každou reakcí se dává záznam do databáze. Nějak to vylepšit? Přijít na způsob jak to udělat
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id in self.caching:

            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            embed = message.embeds[0]
            reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)

            vypis_hlasu = [user.display_name async for user in reaction.users() if not user.id == self.bot.user.id]

            if payload.emoji.name == "✅":
                edit = embed.set_field_at(
                    1,
                    name="Ano, pojedu:",
                    value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}",
                    inline=False)
                await reaction.message.edit(embed=edit)

                sql = """ INSERT INTO `ReactionUsers` (
                    EventEmbedID,
                    ReactionUser) 
                    VALUES (%s, %s)
                """
                val = (payload.message_id, payload.user_id)

                with MySQLWrapper(user=USER, password=PASSWORD, host=HOST, database=DATABASE) as db:
                    db.execute(sql, val, commit=True)

            if payload.emoji.name == "❌":
                edit = embed.set_field_at(
                    2,
                    name="Ne, nejedu:",
                    value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}", inline=False)
                await reaction.message.edit(embed=edit)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id in self.caching:

            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            embed = message.embeds[0]
            reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)

            vypis_hlasu = [user.display_name
                           async for user in reaction.users()
                           if not user.id == self.bot.user.id]

            if payload.emoji.name == "✅":
                edit = embed.set_field_at(
                    1,
                    name="Ano, pojedu:",
                    value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}", inline=False)

                await reaction.message.edit(embed=edit)

            if payload.emoji.name == "❌":
                edit = embed.set_field_at(
                    2,
                    name="Ne, nejedu:",
                    value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}", inline=False)

                await reaction.message.edit(embed=edit)


def setup(bot):
    bot.add_cog(EventSystem(bot))
