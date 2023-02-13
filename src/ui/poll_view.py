import aiomysql.pool
import discord

from src.ui.button import ButtonBackend
from src.ui.poll import Poll


class PollView(discord.ui.View):
    def __init__(self, poll: Poll, embed, db_poll: aiomysql.pool.Pool):
        super().__init__(timeout=None)
        self.poll = poll
        self.embed = embed
        self.db_poll = db_poll
        self.reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        self._add_vote_buttons()

    def _add_vote_buttons(self):
        for index, option in enumerate(self.poll.options):
            self.add_item(ButtonBackend(
                custom_id=f"{index}:{self.poll.message_id}",
                label=f"{option}",
                emoji=self.reactions[index],
                poll=self.poll,
                embed=self.embed,
                index=index,
                db_poll=self.db_poll
            ))
