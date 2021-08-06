from discord.ext import commands


class Error(commands.Cog):
    """Basic class for catching errors and sending a message"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.ExpectedClosingQuoteError):
            await ctx.send("Pozor! Chybí ti někde uvozovka!")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("Chybí ti požadovaná práva!")


def setup(bot):
    bot.add_cog(Error(bot))
