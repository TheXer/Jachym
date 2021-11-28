import json

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions


class Utility(commands.Cog):
    """Class for fun commands and utilities"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Jáchym je ready!")

        await self.bot.change_presence(activity=discord.Game(name=f"Jsem na {len(self.bot.guilds)} serverech!"))

    @commands.command(pass_context=True, aliases=['help'])
    async def pomoc(self, ctx):
        with open("text_json/package.json") as f:
            test = json.load(f)

        embed = discord.Embed.from_dict(test["help"])

        file = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")
        embed.set_thumbnail(url="attachment://LogoPotkani.png")
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        await ctx.send(file=file, embed=embed)

    @commands.command(pass_context=True)
    async def rozcestnik(self, ctx):
        with open("text_json/package.json") as f:
            test = json.load(f)

            embed = discord.Embed.from_dict(test["rozcestnik"])
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
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
