import datetime
import re

import dateparser
import discord
from discord.app_commands import Transformer

from src.ui.error_view import DatetimeNotRecognizedError, TooFewOptionsError, TooManyOptionsError
from src.ui.poll import Poll


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


class DatetimeTransformer(Transformer):
    async def transform(
        self, interaction: discord.Interaction, date_time: str
    ) -> DatetimeNotRecognizedError | datetime.datetime:
        parsed_datetime: datetime.datetime = dateparser.parse(
            date_time,
            languages=["cs", "en", "sk"],
        )

        if not parsed_datetime:
            msg = "Daný datum jsem bohužel nerozpoznal, zkusíš to znova?"
            raise DatetimeNotRecognizedError(msg, interaction)

        if parsed_datetime < datetime.datetime.now():
            msg = "Datum nemůžeš zakládat v minulosti!"
            raise DatetimeNotRecognizedError(msg, interaction)

        if parsed_datetime.time() == "00:00:00":
            parsed_datetime = parsed_datetime + datetime.timedelta(hours=12, minutes=00)

        return parsed_datetime
