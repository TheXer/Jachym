import re

import discord
from discord import app_commands
from discord.app_commands import Transform, Transformer
from discord.ext import commands
from loguru import logger

from src.db_folder.databases import PollDatabase, VoteButtonDatabase
from src.jachym import Jachym
from src.ui.embeds import PollEmbed, PollEmbedBase
from src.ui.error_view import TooFewOptionsError, TooManyOptionsError
from src.ui.poll import Poll
from src.ui.poll_view import PollView


class OptionsTransformer(Transformer):
    async def transform(
        self, interaction: discord.Interaction, option: str
    ) -> TooManyOptionsError | TooFewOptionsError | list[str]:
        """
        Transformer method to transformate a single string to multiple options. If they are not within parameters,
        raises an error, else returns options.

        Parameters
        ----------
            interaction: discord.Interaction
            option: str

        Returns
        -------
            List of strings

        Raises:
        -------
            TooManyOptionsError, TooFewOptionsError

        """
        answers = [option for option in re.split('"|"|“|„', option) if option.strip()]
        if len(answers) > Poll.MAX_OPTIONS:
            msg = f"Zadal jsi příliš mnoho odpovědí, můžeš maximálně {Poll.MAX_OPTIONS}!"
            raise TooManyOptionsError(msg, interaction)
        if len(answers) < Poll.MIN_OPTIONS:
            msg = f"Zadal jsi příliš málo odpovědí, můžeš alespoň {Poll.MIN_OPTIONS}!"
            raise TooFewOptionsError(msg, interaction)
        return answers


class PollCreate(commands.Cog):
    def __init__(self, bot: Jachym):
        self.bot = bot

    @app_commands.command(
        name="anketa",
        description="Anketa pro hlasování. Jsou vidět všichni hlasovatelé.",
    )
    @app_commands.rename(question="otázka", answer="odpovědi")
    @app_commands.describe(
        question="Otázka, kterou chceš položit.",
        answer='Odpovědi, rozděluješ odpovědi uvozovkou ("), maximálně pouze 10 možností',
    )
    async def pool(
        self,
        interaction: discord.Interaction,
        question: str,
        answer: Transform[list[str, ...], OptionsTransformer],
    ) -> discord.Message:
        await interaction.response.send_message(embed=PollEmbedBase("Nahrávám anketu..."))
        message = await interaction.original_response()

        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answer,
            user_id=interaction.user.id,
        )

        embed = PollEmbed(poll)
        view = PollView(poll, embed, db_poll=self.bot.pool)
        await PollDatabase(self.bot.pool).add(poll)
        await VoteButtonDatabase(self.bot.pool).add_options(poll)

        self.bot.active_discord_polls.add(poll)
        await self.bot.set_presence()
        logger.info(f"Successfully added Pool - {message.id}")
        return await message.edit(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
