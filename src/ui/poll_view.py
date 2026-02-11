import discord
from src.ui.button import (
    VoteButton,
    NewOptionButton,
    RemoveOptionButton,
    ClosePollButton,
    SubscribeButton,
)
from src.ui.embeds import PollEmbed
from src.ui.emojis import NUMBER_EMOJIS


class PollView(discord.ui.View):
    """Poll View that renders one `VoteButton` per `PollOption`.

    Parameters
    - poll: tortoise.models.Poll instance
    - options: iterable of PollOption instances (ordered)
    - embed: PollEmbed instance
    """

    def __init__(self, poll, options, embed: PollEmbed):
        super().__init__(timeout=None)
        self.poll = poll
        self.embed = embed
        self.options = list(options)

        for index, option in enumerate(self.options):
            btn = VoteButton(
                poll_id=poll.id,
                option_id=option.id,
                index=index,
                label=option.text,
                emoji=NUMBER_EMOJIS[index],
                embed=embed,
            )
            self.add_item(btn)

        # Add button to allow adding new option (permission checked inside button/modal)
        self.add_item(NewOptionButton(poll, self.options, embed, self))
        # Add button to allow removing an option
        self.add_item(RemoveOptionButton(poll, self.options, embed, self))
        # Add button to close poll and show results
        self.add_item(ClosePollButton(poll, self.options, embed, self))
        # Add button to subscribe to poll results
        self.add_item(SubscribeButton(poll))
