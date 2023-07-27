import datetime
import re

import dateparser
import discord
from discord import app_commands
from discord.app_commands import Transform, Transformer
from discord.ext import commands
from loguru import logger

from src.db_folder.databases import PollDatabase, VoteButtonDatabase
from src.jachym import Jachym
from src.ui.embeds import PollEmbed, PollEmbedBase
from src.ui.error_view import DatetimeNotRecognizedError, TooFewOptionsError, TooManyOptionsError
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
            msg = f"Zadal jsi příliš málo odpovědí, zadej alespoň {Poll.MIN_OPTIONS}!"
            raise TooFewOptionsError(msg, interaction)
        return answers


class DatetimeTransformer(Transformer):
    async def transform(self, interaction: discord.Interaction, date_time: str) -> datetime.datetime:
        parsed_datetime = dateparser.parse(
            date_time,
            languages=["cs", "en", "sk"],
        )
        if not parsed_datetime:
            msg = "Daný datum jsem bohužel nerozpoznal, zkusíš to znova?"
            raise DatetimeNotRecognizedError(msg, interaction)
        if parsed_datetime < datetime.datetime.now():
            msg = "Datum nemůžeš zakládat v minulosti!"
            raise DatetimeNotRecognizedError(msg, interaction)
        return parsed_datetime


class PollCreate(commands.Cog):
    POLL_PARAMETERS = {
        "name": "anketa",
        "description": "Anketa pro hlasování. Jsou vidět všichni, kteří se zapojili.",
        "question": "Otázka, na kterou potřebuješ znát odpověď",
        "answers": f'Odpovědi, odpovědi rozděluj uvozovkami ("), maximálně až {Poll.MAX_OPTIONS} možností',
        "date_time": "Datum, kdy anketa skončí",
        "help":
            f"""
            Jednoduchá anketa, která obsahuje otázku a odpovědi. Povoleno je až {Poll.MAX_OPTIONS} možností. 
            """
    }

    def __init__(self, bot: Jachym):
        self.bot = bot

    @app_commands.command(
        name=POLL_PARAMETERS["name"],
        description=POLL_PARAMETERS["description"],
    )
    @app_commands.rename(
        question="otázka",
        answer="odpovědi",
        date_time="datum",
    )
    @app_commands.describe(
        question=POLL_PARAMETERS["question"],
        answer=POLL_PARAMETERS["answers"],
        date_time=POLL_PARAMETERS["date_time"],
    )
    async def pool(
        self,
        interaction: discord.Interaction,
        question: str,
        answer: Transform[list[str, ...], OptionsTransformer],
        date_time: Transform[datetime.datetime, DatetimeTransformer] | None,
    ) -> discord.Message:
        await interaction.response.send_message(embed=PollEmbedBase("Nahrávám anketu..."))
        message = await interaction.original_response()

        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answer,
            user_id=interaction.user.id,
            date_created=date_time,
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
