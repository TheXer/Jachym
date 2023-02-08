import aiomysql.pool
import discord

from poll_design.button import ButtonBackend
from poll_design.poll import Poll


class PollView(discord.ui.View):
    def __init__(self, poll: Poll, embed, db_poll: aiomysql.pool.Pool):
        super().__init__(timeout=None)
        self.poll = poll
        self.embed = embed
        self.db_poll = db_poll
        self._add_vote_buttons()

    def _add_vote_buttons(self):
        for index, option in enumerate(self.poll.options):
            self.add_item(ButtonBackend(
                custom_id=f"{index}:{self.poll.message_id}",
                label=f"{index + 1}",
                poll=self.poll,
                embed=self.embed,
                index=index,
                db_poll=self.db_poll
            ))


class PollInitialization(discord.ui.View):
    # this class should handle initialization of all polls
    pass
