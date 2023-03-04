import datetime

from discord import Message
from discord.ext import commands

from src.ui.embeds import EmbedFromJSON


class Utility(commands.Cog):
    """Class for fun commands and utilities"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=['help'])
    async def pomoc(self, ctx: commands.Context) -> Message:
        embed = EmbedFromJSON().add_fields_from_json("help")
        return await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def rozcestnik(self, ctx: commands.Context) -> Message:
        embed = EmbedFromJSON().add_fields_from_json("rozcestnik")
        return await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def ping(self, ctx: commands.Context) -> Message:
        ping = round(self.bot.latency * 1000)
        if ping < 200:
            message = f'🟢 {ping} milisekund.'
        elif 200 < ping < 400:
            message = f'🟡 {ping} milisekund.'
        else:
            message = f'🔴 {ping} milisekund.'

        return await ctx.send(message)

    @commands.command(pass_context=True, aliases=["smazat"])
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx: commands.Context, limit: int) -> Message:
        await ctx.message.delete()
        if 1 < limit < 100:
            deleted = await ctx.channel.purge(limit=limit)
            return await ctx.send("Smazáno {deleted} zpráv.".format(deleted=len(deleted)))
        else:
            return await ctx.send("Limit musí být někde mezi 1 nebo 99!")

    @commands.command()
    async def time(self, ctx: commands.Context):
        return await ctx.send(str(datetime.datetime.now()))

    @commands.command(aliases=["narozeniny"])
    async def birthday(self, ctx):
        today = datetime.date.today()
        bot_birthday = datetime.datetime.strptime(self.bot.MY_BIRTHDAY, "%d.%m.%Y").replace(year=today.year)
        days_until_birthday = (bot_birthday.date() - today).days
        await ctx.send(
            f"Moje narozeniny jsou 27. prosince 2020 a zbývá přesně {days_until_birthday} dní do mých narozenin!")


async def setup(bot):
    await bot.add_cog(Utility(bot))
