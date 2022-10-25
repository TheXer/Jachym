import datetime
import json

import discord
from discord import Message
from discord import app_commands
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
        return embed

    # zkouška, funguje to, pokračovat v tom
    @app_commands.command(name="pomoc")
    async def my_private_command(self, interaction: discord.Interaction) -> None:
        """ Pomocníček na vše  """
        file = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")
        embed = self.json_to_embed("help")
        embed.set_thumbnail(url="attachment://LogoPotkani.png")
        await interaction.response.send_message(file=file, embed=embed, ephemeral=True)

    @commands.command(pass_context=True, aliases=['help'])
    async def pomoc(self, ctx: commands.Context) -> Message:
        file = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")
        embed = self.json_to_embed("help")
        embed.set_thumbnail(url="attachment://LogoPotkani.png")
        return await ctx.send(file=file, embed=embed)

    @commands.command(pass_context=True)
    async def rozcestnik(self, ctx: commands.Context) -> Message:
        embed = self.json_to_embed("rozcestnik")
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
    @has_permissions(administrator=True)
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


async def setup(bot):
    await bot.add_cog(Utility(bot))
