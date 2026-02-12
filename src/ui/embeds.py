import json
import pathlib
from datetime import datetime

import discord
from discord.colour import Color, Colour

from src.ui.emojis import NUMBER_EMOJIS, ScoutEmojis
from typing import Iterable


class ErrorMessage(discord.Embed):
    """Whether an error occurs, this embed is sent."""

    def __init__(self, message: str):
        title = "⚠️ Jejda, někde se stala chyba..."

        description = (
            f"{message}\n\n"
            f"{ScoutEmojis.FLEUR_DE_LIS.value} *Pokud máš pocit, že tohle by chyba být neměla, "
            f"napiš [sem](https://github.com/TheXer/Jachym/issues/new/choose)*"
        )

        self.set_footer(text="Uděláno s ♥!")

        super().__init__(
            title=title,
            description=description,
            colour=Colour.red(),
            timestamp=datetime.now(),
        )


class PollEmbedBase(discord.Embed):
    def __init__(self, question) -> None:
        super().__init__(title=f"📊 {question}", colour=Color.blue())
        self.set_footer(text="Momentální verze běží na beta verzi! Očekávej nějaké chyby sem a tam.")


class PollEmbed(PollEmbedBase):
    """Base Embed view for Poll objects.

    Accepts a question string and an iterable of options (either strings or PollOption
    instances)."""

    def __init__(self, question: str, options: Iterable, created_at: datetime | None = None):
        super().__init__(question)
        self.answers = list(options)
        self._add_options()
        self.timestamp = datetime.now()

        if created_at is not None:
            self._add_timestamp(created_at)

    def _add_options(self):
        for index, option in enumerate(self.answers):
            label = option.text if hasattr(option, "text") else str(option)
            self.add_field(
                name=f"{NUMBER_EMOJIS[index]} {label}",
                value="**0** |",
                inline=False,
            )

    def _add_timestamp(self, timestamp: datetime):
        unix_time = discord.utils.format_dt(timestamp, "R")
        self.add_field(
            name="",
            value=f"Anketa vyprší {unix_time}",
            inline=False,
        )


class EmbedFromJSON(discord.Embed):
    PATH = pathlib.Path("src/text_json/cz_text.json")
    PICTURE = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")

    def __init__(self):
        super().__init__(colour=Color.blue())

    @classmethod
    def add_fields_from_json(cls, root_path):
        with pathlib.Path.open(cls.PATH) as f:
            text = json.load(f)[root_path]
            em = EmbedFromJSON().from_dict(text)
            em.set_thumbnail(url="attachment://LogoPotkani.png")
            return em
