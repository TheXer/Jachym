import discord
from discord.colour import Color

from poll_design.poll import Poll


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
