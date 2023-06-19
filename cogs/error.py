from discord import Interaction
from discord.app_commands import CommandInvokeError
from discord.ext import commands
from loguru import logger


class PrettyError(CommandInvokeError):
    def __init__(self, message: str, interaction: Interaction, inner_exception: Exception | None = None):
        super().__init__(interaction.command, inner_exception)
        self.message = message
        self.interaction = interaction

    async def send(self):
        send_args = {
            "content": f"{self.message}",
            "ephemeral": False,
        }
        if not self.interaction.response.is_done():
            await self.interaction.response.send_message(**send_args)
        else:
            await self.interaction.followup.send(**send_args)


class TooManyOptionsError(PrettyError):
    pass


class TooFewOptionsError(PrettyError):
    pass


class Error(commands.Cog):
    """Basic class for catching errors and sending a message"""

    def __init__(self, bot):
        self.bot = bot
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: Interaction, error: Exception):
        match error:
            case PrettyError():
                # if I use only 'error', gives me NoneType. Solved by this
                logger.error(f"{error.__class__.__name__}: {interaction.command.name}")
                await error.send()
            case _:
                logger.critical(error)


async def setup(bot):
    await bot.add_cog(Error(bot))
