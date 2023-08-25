from discord import Interaction
from discord.ext import commands
from loguru import logger

from src.ui.embeds import ErrorMessage
from src.ui.error_view import PrettyError


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
                await interaction.response.send_message(
                    embed=ErrorMessage(
                        "Tato zpráva by se nikdy zobrazit správně neměla. "
                        "Jsi borec, že jsi mi dokázal rozbít Jáchyma, nechceš mi o tom napsat do issues na githubu?"
                    )
                )


async def setup(bot):
    await bot.add_cog(Error(bot))
