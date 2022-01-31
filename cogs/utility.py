import json
from itertools import cycle

import discord
from discord import Message
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions


class Utility(commands.Cog):
    """Class for fun commands and utilities"""

    def __init__(self, bot):
        self.bot = bot

        # TODO: BUG: Cycle z nějakého důvodu nezobrazuje správně self.bot.guilds, vždy se ukáže 0. Pořešit.
        self.news = cycle([
            f"Jsem na {len(self.bot.guilds)} serverech!",
            "Pomoc? !help",
        ])

        self.pressence.start()

    def json_to_embed(self, root_name: str) -> discord.Embed:
        with open("text_json/cz_text.json") as f:
            text = json.load(f)
        embed = discord.Embed.from_dict(text[root_name])
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        return embed

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

    @tasks.loop(seconds=5)
    async def pressence(self):
        # proč tady? https://stackoverflow.com/questions/59126137/how-to-change-discord-py-bot-activity

        await self.bot.change_presence(
            activity=discord.Game(
                name=next(self.news)
            )
        )

    @pressence.before_loop
    async def before_cache(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Utility(bot))
