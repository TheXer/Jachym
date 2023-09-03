import discord
from discord import Interaction, InteractionResponse
from discord.app_commands import CommandInvokeError
from discord.ui import Item
from loguru import logger

from src.ui.embeds import ErrorMessage


class PrettyError(CommandInvokeError):
    """Pretty errors useful for raise keyword"""

    def __init__(self, message: str, interaction: Interaction, inner_exception: Exception | None = None):
        super().__init__(interaction.command, inner_exception)
        self.message = message
        self.interaction = interaction

    async def send(self) -> InteractionResponse:
        if not self.interaction.response.is_done():
            return await self.interaction.response.send_message(embed=ErrorMessage(self.message), ephemeral=True)
        return await self.interaction.followup.send(embed=ErrorMessage(self.message), ephemeral=True)


class ErrorView(discord.ui.View):
    async def on_error(self, interaction: Interaction, error: Exception, item: Item) -> InteractionResponse:
        logger.error(f"{item.__class__.__name__} raised an error: {str(error)}")
        return await interaction.response.send_message(embed=ErrorMessage(str(error)), ephemeral=True)


class TooManyOptionsError(PrettyError):
    """Whether the view has too many options."""

    pass


class TooFewOptionsError(PrettyError):
    """Whether the view has too few options."""

    pass


class NoPermissionError(PrettyError):
    """Whether the user has no permissions to edit."""

    pass


class DatetimeNotRecognizedError(PrettyError):
    """Whether the datetime is not recognized."""

    pass
