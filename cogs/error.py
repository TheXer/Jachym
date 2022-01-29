import logging

from discord import Message
from discord.ext import commands


class Error(commands.Cog):
    """Basic class for catching errors and sending a message"""

    def __init__(self, bot):
        self.bot = bot

        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(handler)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> Message | None:
        if isinstance(error, commands.ExpectedClosingQuoteError):
            return await ctx.send("Pozor! Chybí ti někde uvozovka!")

        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send("Chybí ti požadovaná práva!")

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Chybí ti povinný argument, zkontroluj si ho znova!")

        else:
            self.logger.critical(f"{ctx.message.id}, {ctx.message.content} | {error}")

            return await ctx.send(
                f"O této chybě ještě nevím a nebyla zaznamenána. Napiš The Xero#1273 o této chybě.\n"
                f"Text chyby: `{error}`\n"
                f"Číslo chyby: `{ctx.message.id}`"
            )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.logger.info(f"{ctx.message.id} {ctx.message.content}")


def setup(bot):
    bot.add_cog(Error(bot))
