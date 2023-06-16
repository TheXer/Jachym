from discord.ext import commands
from loguru import logger

from src.ui.error_handling import EmbedBaseError


class Error(commands.Cog):
    """Basic class for catching errors and sending a message"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ):
        match error:
            case EmbedBaseError():
                logger.error(error)
                return await error.send()

            case commands.MissingPermissions():
                logger.error(f"Missing Permissions: {error}")
                return await ctx.send("Chybí ti požadovaná práva!")

            case commands.CommandNotFound():
                return None

            case _:
                logger.critical(f"Catched an error: {error}")
                return None


async def setup(bot):
    await bot.add_cog(Error(bot))
