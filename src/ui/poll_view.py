import datetime

import aiomysql.pool
import discord

from src.ui.button import ButtonBackend
from src.ui.poll import Poll


class PollView(discord.ui.View):
    REACTIONS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    def __init__(self, poll: Poll, embed, db_poll: aiomysql.pool.Pool):
        super().__init__(timeout=None)
        self.poll = poll
        self.embed = embed
        self.db_poll = db_poll
        self.add_buttons()

    def add_buttons(self):
        for index, option in enumerate(self.poll.options):
            button = ButtonBackend(
                custom_id=f"{index}:{self.poll.message_id}",
                label=f"{option}",
                emoji=self.REACTIONS[index],
                poll=self.poll,
                embed=self.embed,
                index=index,
                db_poll=self.db_poll)

            self.add_item(button)

    def check_date_difference(self) -> bool:
        date_deletion = self.poll.created_at + datetime.timedelta(days=25)
        return datetime.date.today() > date_deletion
