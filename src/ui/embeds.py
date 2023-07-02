import json
import pathlib
from datetime import datetime

import discord
from discord.colour import Color, Colour

from src.ui.emojis import ScoutEmojis
from src.ui.poll import Poll


class ErrorMessage(discord.Embed):
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


class PollEmbed(PollEmbedBase):
    REACTIONS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def __init__(self, poll: Poll):
        super().__init__(poll.question)
        self.answers = poll.options
        self._add_options()

        self.set_footer(text="Uděláno s ♥!")
        self.timestamp = datetime.now()

    def _add_options(self):
        for index, option in enumerate(self.answers):
            self.add_field(
                name=f"{self.REACTIONS[index]} {option}",
                value="**0** |",
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
