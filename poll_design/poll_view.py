import discord

from poll_design.button import ButtonBackend
from poll_design.poll import Poll
from ui.poll_embed import PollEmbed


class PollView(discord.ui.View):
    def __init__(self, poll: Poll, embed: PollEmbed):
        super().__init__(timeout=None)
        self.poll = poll
        self.embed = embed
        self._add_vote_buttons()

    def _add_vote_buttons(self):
        for index, option in enumerate(self.poll.options):
            self.add_item(ButtonBackend(
                custom_id=f"{index}:{self.poll.message_id}",
                label=f"{index + 1}",
                message_id=self.poll.message_id,
                channel_id=self.poll.channel_id,
                embed=self.embed,
                index=index
            ))
