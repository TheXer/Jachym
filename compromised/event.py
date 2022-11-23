import datetime
import json

import discord
from discord import Message
from discord.ext import commands, tasks

from db_folder.sqldatabase import AioSQL


class EventSystem(commands.Cog):
    """Class for event system, creating pools and sending a message on exact day"""

    def __init__(self, bot):
        self.bot = bot
        self.pool = self.bot.pool
        self.caching = set()

        self.cache.start()
        self.send_events.start()

        # Pro pretty-print dnů v týdnu, páč z nějakýho důvodu ten lokální na mašině nejede jak má. Řešeno tímto.
        self.weekdays = {
            "Monday": "Pondělí",
            "Tuesday": "Úterý",
            "Wednesday": "Středa",
            "Thursday": "Čtvrtek",
            "Friday": "Pátek",
            "Saturday": "Sobota",
            "Sunday": "Neděle"
        }

    # Caching systém, oproti caching systému ve poll.py se tento vždy smaže pokud je event odeslán a zpracován.
    @tasks.loop(minutes=30)
    async def cache(self) -> set[int, ...]:
        async with AioSQL(self.pool) as db:
            query = "SELECT `EventEmbedID` FROM `EventPlanner`"
            tuples = await db.query(query=query)

            self.caching = {
                int(clean_variable)
                for variable in tuples
                for clean_variable in variable}

            return self.caching

    @cache.before_loop
    async def before_cache(self):
        await self.bot.wait_until_ready()

    # Ověřuje databázi jestli něco není starší než dané datum a pak jej pošle. Změněno na 1 minutu, něco mi tam shazuje
    # connection k databázi
    @tasks.loop(minutes=1)
    async def send_events(self):
        async with AioSQL(self.pool) as db:

            sql = "SELECT * FROM EventPlanner;"
            result = await db.query(query=sql)

            for GuildID, EventID, EventTitle, EventDescription, EventDate, ChannelID in result:
                if EventDate > datetime.datetime.now():
                    continue
                try:
                    sql = "SELECT ReactionUser FROM ReactionUsers WHERE EventEmbedID = %s;"
                    result = await db.query(query=sql, val=(EventID,))

                    members = {
                        await self.bot.fetch_user(int(x))
                        for ID in result
                        for x in ID}

                    embed = discord.Embed(
                        title=f"**Pořádá se akce:** \n{EventTitle}",
                        description=f"{EventDescription}",
                        colour=discord.Colour.gold())

                    file = discord.File("fotky/trojuhelnik.png", filename="trojuhelnik.png")
                    embed.set_thumbnail(url="attachment://trojuhelnik.png")

                    if len(members) == 0:
                        embed.add_field(name="Účastníci", value="Nikdo nejede.")
                    else:
                        embed.add_field(name="Účastníci", value=f"{','.join(user.mention for user in members)}")

                    channel = self.bot.get_channel(int(ChannelID))
                    await channel.send(file=file, embed=embed)

                    sql2 = "DELETE FROM EventPlanner WHERE EventEmbedID = %s;"
                    await db.execute(sql2, (EventID,), commit=True)

                    msg = await channel.fetch_message(EventID)
                    await msg.delete()
                except discord.errors.NotFound:
                    sql2 = "DELETE FROM EventPlanner WHERE EventEmbedID = %s;"
                    await db.execute(sql2, (EventID,), commit=True)

    @send_events.before_loop
    async def before_send_events(self):
        await self.bot.wait_until_ready()

    # help systém pro to.
    @commands.group(invoke_without_command=True)
    async def udalost(self, ctx: commands.Context) -> Message:
        with open("text_json/cz_text.json") as f:
            test = json.load(f)

        embed = discord.Embed.from_dict(test["udalost"])
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        return await ctx.send(embed=embed)

    @udalost.command()
    async def create(self, ctx: commands.Context, title: str, description: str, eventdatetime: str) -> Message:

        datetime_formatted = datetime.datetime.strptime(eventdatetime, '%d.%m.%Y %H:%M')

        if datetime.datetime.now() > datetime_formatted:
            return await ctx.send("Nemůžeš zakládat událost, která se stala v minulosti!")

        await ctx.message.delete()
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.gold())
        embed.add_field(name="Datum",
                        value=f"{self.weekdays[datetime_formatted.strftime('%A')]}, "
                              f"{datetime_formatted:%d.%m.%Y %H:%M}")

        embed.add_field(name="Ano, pojedu:", value="0 |", inline=False)
        embed.add_field(name="Ne, nejedu:", value="0 |", inline=False)
        embed.add_field(name="Ještě nevím:", value="0 |", inline=False)
        reactions = ["✅", "❌", "❓"]

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

        async with AioSQL(self.pool) as db:
            await db.execute(sql, val, commit=True)

        self.caching.add(sent.id)

    @udalost.command()
    async def vypis(self, ctx: commands.Context) -> Message:
        sql = """
            SELECT EventTitle, EventDescription, EventDate 
            FROM EventPlanner 
            WHERE GuildID = %s
            ORDER BY EventDate; """

        async with AioSQL(self.pool) as db:
            result = await db.query(query=sql, val=(ctx.guild.id,))
            embed = discord.Embed(title="Výpis všech událostí", colour=discord.Colour.gold())

        for title, description, date in result:
            embed.add_field(
                name=title,
                value=f"{self.weekdays[date.strftime('%A')]}, {date: %d.%m.%Y %H:%M}\n{description}",
                inline=False)

        return await ctx.send(embed=embed)

    # Smaže event z databáze pomocí ID embedu. Přijít na lepší způsob?
    @udalost.command(aliases=["delete"])
    async def smazat(self, ctx: commands.Context, embed: Message):
        async with AioSQL(self.pool) as db:
            try:
                sql = "DELETE FROM EventPlanner WHERE EventEmbedID = %s;"
                await db.execute(sql, (embed.id,), commit=True)

                msg = await ctx.fetch_message(embed.id)
                await msg.delete()

                await ctx.send("Úspěšně smazán event")

            except discord.errors.NotFound:
                await ctx.send("Zkontroluj si číslo, páč tento není v mé paměti. Možná jsi to blbě napsal?")

    # To stejné, akorát s každou reakcí se dává záznam do databáze. Nějak to vylepšit? Přijít na způsob jak to udělat
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> Message:
        if payload.message_id in self.caching:

            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            embed = message.embeds[0]
            reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)

            vypis_hlasu = [
                user.display_name
                async for user in reaction.users()
                if not user.id == self.bot.user.id
            ]

            match payload.emoji.name:
                case "✅":
                    edit = embed.set_field_at(
                        1,
                        name="Ano, pojedu:",
                        value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}",
                        inline=False)

                    async with AioSQL(self.pool) as db:
                        sql = """ INSERT INTO `ReactionUsers` (
                                            EventEmbedID,
                                            ReactionUser
                                        ) VALUES (%s, %s)"""
                        val = (payload.message_id, payload.user_id)
                        await db.execute(sql, val, commit=True)

                    return await reaction.message.edit(embed=edit)

                case "❌":
                    edit = embed.set_field_at(
                        2,
                        name="Ne, nejedu:",
                        value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}",
                        inline=False)

                    return await reaction.message.edit(embed=edit)

                case "❓":
                    edit = embed.set_field_at(
                        3,
                        name="Ještě nevím:",
                        value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}", inline=False)

                    return await reaction.message.edit(embed=edit)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> Message:
        if payload.message_id in self.caching:

            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            embed = message.embeds[0]
            reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)

            vypis_hlasu = [user.display_name
                           async for user in reaction.users()
                           if not user.id == self.bot.user.id]

            match payload.emoji.name:
                case "✅":
                    edit = embed.set_field_at(
                        1,
                        name="Ano, pojedu:",
                        value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}",
                        inline=False)

                    return await reaction.message.edit(embed=edit)

                case "❌":
                    edit = embed.set_field_at(
                        2,
                        name="Ne, nejedu:",
                        value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}",
                        inline=False)

                    return await reaction.message.edit(embed=edit)

                case "❓":
                    edit = embed.set_field_at(
                        3,
                        name="Ještě nevím:",
                        value=f"{len(vypis_hlasu)} | {', '.join(vypis_hlasu)}", inline=False)

                    return await reaction.message.edit(embed=edit)


async def setup(bot):
    await bot.add_cog(EventSystem(bot))
