from discord.ext import commands

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
                return await error.send()

            case commands.MissingPermissions():
                return await ctx.send("Chybí ti požadovaná práva!")

            case commands.CommandNotFound():
                return None

            case _:
                self.logger.critical(
                    f"{ctx.message.id}, {ctx.message.content} | {error}",
                )
                print(error)
                return None

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        self.logger.info(f"{ctx.message.id} {ctx.message.content}")


async def setup(bot):
    await bot.add_cog(Error(bot))
