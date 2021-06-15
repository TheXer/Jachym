from discord.ext import commands


# Placeholder for future statictics
class Statictics(commands.Cog):
    pass


def setup(bot):
    bot.add_cog(Statictics(bot))
