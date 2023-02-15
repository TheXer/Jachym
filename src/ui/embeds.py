import datetime
import json

import discord
from discord.colour import Color

from src.ui.poll import Poll


class PollEmbedBase(discord.Embed):
    def __init__(self, question) -> None:
        super().__init__(
            title=f"📊 {question}",
            colour=Color.blue()
        )


class PollEmbed(PollEmbedBase):
    def __init__(self, poll: Poll):
        super().__init__(poll.question)
        self.answers = poll.options
        self.reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        self._add_options()

    def _add_options(self):
        for index, option in enumerate(self.answers):
            self.add_field(
                name=f"{self.reactions[index]} {option}",
                value="**0** |",
                inline=False
            )


class EmbedFromJSON(discord.Embed):
    PATH = "src/text_json/cz_text.json"
    PICTURE = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")

    def __init__(self):
        super().__init__(
            colour=Color.blue(),
            timestamp=datetime.datetime.now())

    @classmethod
    def add_fields_from_json(cls, root_path):
        with open(cls.PATH, "r") as f:
            text = json.load(f)[root_path]
        return EmbedFromJSON.from_dict(text)
