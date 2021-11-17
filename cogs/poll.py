import datetime

import discord
from discord.ext import commands, tasks

from db_folder.sqldatabase import SQLDatabase


class Poll(commands.Cog):
    """Class for Poll system"""
    def __init__(self, bot):
        self.bot = bot

        self.cache.start()
        self.caching = set()

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

            vypis_hlasu = [
                user.display_name
                async for user in reaction.users()
                if not user.id == self.bot.user.id]

            edit = embed.set_field_at(
                i,
                name=embed.fields[i].name,
                value=f"**{len(vypis_hlasu)}** | {', '.join(vypis_hlasu)}",
                inline=False)
            await reaction.message.edit(embed=edit)

    @commands.command()
    async def anketa(self, ctx, question, *answer: str):
        await ctx.message.delete()

        if question is None:
            return await ctx.send("Nemáš žádnou otázku!")

        if len(answer) > 10:
            return await ctx.send("Zadal jsi příliš mnoho odpovědí, maximum je 10!")

        elif len(answer) in (0, 1):
            return await ctx.send("Nezadal jsi žádnou odpověď nebo příliš málo odpovědí, musíš mít minimálně dvě!")

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

            with SQLDatabase() as db:
                sql = "INSERT INTO `Poll`(PollID, DateOfPoll) VALUES (%s, %s)"
                val = (sent.id, datetime.datetime.now())

                db.execute(sql, val, commit=True)

            self.caching.add(sent.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_add_remove(payload=payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.reaction_add_remove(payload=payload)

    # Caching systém pro databázi, ať discord bot nebombarduje furt databázi a vše udržuje ve své paměti
    @tasks.loop(minutes=30)
    async def cache(self):
        with SQLDatabase() as db:
            # Query pro to, aby se každý záznam, který je starší než měsíc, smazal
            query2 = "DELETE FROM `Poll` WHERE `DateOfPoll` < CURRENT_DATE - 30;"
            db.execute(query2, commit=True)

            query = "SELECT `PollID` FROM `Poll`"
            tuples = db.query(query=query)

            # ořezání všeho co tam je, předtím to bylo ve tvaru [('987234', ''..)]
            self.caching = {
                int(clean_variable)
                for variable in tuples
                for clean_variable in variable}

            return self.caching

    @cache.before_loop
    async def before_cache(self):
        with SQLDatabase() as db:
            query = """
                CREATE TABLE IF NOT EXISTS `Poll` (
                ID_Row INT NOT NULL AUTO_INCREMENT,
                PollID VARCHAR(255) NOT NULL,
                DateOfPoll DATE NOT NULL,
                PRIMARY KEY (ID_Row))"""
            db.execute(query)
            print("Table Poll OK")

        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Poll(bot))
