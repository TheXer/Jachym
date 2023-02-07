import logging

from discord.ext import commands


# for finding errors with the code.
# TODO: SPRAV TO UŽ!!!!!

class Error(commands.Cog):
    """Basic class for catching errors and sending a message"""

    def __init__(self, bot):
        self.bot = bot

        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.WARN)
        handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(handler)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.ExpectedClosingQuoteError):
            return await ctx.send(f"Pozor! Chybí tady: {error.close_quote} uvozovka!")

        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send("Chybí ti požadovaná práva!")

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Chybí ti povinný argument, zkontroluj si ho znova!")

        else:
            # self.logger.critical(f"{ctx.message.id}, {ctx.message.content} | {error}")

            print(error)

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        self.logger.info(f"{ctx.message.id} {ctx.message.content}")


async def setup(bot):
    await bot.add_cog(Error(bot))
