import json
from datetime import datetime

import discord
from discord.colour import Color

from src.ui.poll import Poll


class CooldownErrorEmbed(discord.Embed):
    def __init__(self, seconds: float):
        self.seconds = round(seconds)

        super().__init__(
            title=f"⚠️ Vydrž! Další anketu můžeš založit za {self.correct_czech_writing()}! ⚠️",
            colour=Color.red()
        )

    def correct_czech_writing(self) -> str:
        if self.seconds > 4:
            return f"{self.seconds} sekund"
        elif 4 >= self.seconds > 1:
            return f"{self.seconds} sekundy"
        else:
            return "sekundu"


class PollEmbedBase(discord.Embed):
    def __init__(self, question) -> None:
        super().__init__(
            title=f"📊 {question}",
            colour=Color.blue()
        )


class PollEmbed(PollEmbedBase):
    REACTIONS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    def __init__(self, poll: Poll):
        super().__init__(poll.question)
        self.answers = poll.options
        self._add_options()
        self._add_timestamp()

    def _add_options(self):
        for index, option in enumerate(self.answers):
            self.add_field(
                name=f"{self.REACTIONS[index]} {option}",
                value="**0** |",
                inline=False
            )

    def _add_timestamp(self):
        self.add_field(
            name="",
            value=f"Anketa byla vytvořena {discord.utils.format_dt(datetime.now(), 'R')}",
            inline=False
        )


class EmbedFromJSON(discord.Embed):
    PATH = "src/text_json/cz_text.json"
    PICTURE = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")

    def __init__(self):
        super().__init__(
            colour=Color.blue())

    @classmethod
    def add_fields_from_json(cls, root_path):
        with open(cls.PATH, "r") as f:
            text = json.load(f)[root_path]
        return EmbedFromJSON.from_dict(text)
