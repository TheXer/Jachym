from discord.ext import commands


class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.ExpectedClosingQuoteError):
            await ctx.send("Pozor! Chybí ti někde uvozovka!")


def setup(bot):
    bot.add_cog(Error(bot))
