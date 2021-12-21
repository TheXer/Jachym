import json

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions


class Utility(commands.Cog):
    """Class for fun commands and utilities"""

    def __init__(self, bot):
        self.bot = bot

    def json_to_embed(self, root_name: str) -> discord.Embed:
        with open("text_json/cz_text.json") as f:
            text = json.load(f)
        embed = discord.Embed.from_dict(text[root_name])
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        return embed

    @commands.command(pass_context=True, aliases=['help'])
    async def pomoc(self, ctx):
        file = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")
        embed = self.json_to_embed("help")
        embed.set_thumbnail(url="attachment://LogoPotkani.png")
        await ctx.send(file=file, embed=embed)

    @commands.command(pass_context=True)
    async def rozcestnik(self, ctx):
        embed = self.json_to_embed("rozcestnik")
        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def ping(self, ctx):
        ping = round(self.bot.latency * 1000)
        if ping < 200:
            await ctx.send(f'🟢 {ping} milisekund.')
        elif 200 < ping < 400:
            await ctx.send(f'🟡 {ping} milisekund.')
        else:
            await ctx.send(f'🔴 {ping} milisekund.')

    @commands.command(pass_context=True, aliases=["smazat"])
    @has_permissions(administrator=True)
    async def clear(self, ctx, limit: int):
        await ctx.message.delete()
        if 1 < limit < 100:
            deleted = await ctx.channel.purge(limit=limit)
            await ctx.send("Smazáno {deleted} zpráv.".format(deleted=len(deleted)))
        else:
            await ctx.send("Limit musí být někde mezi 1 nebo 99!")


def setup(bot):
    bot.add_cog(Utility(bot))
