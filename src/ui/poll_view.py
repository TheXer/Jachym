import aiomysql.pool

from src.ui.button import ButtonBackend, NewOptionButton
from src.ui.embeds import PollEmbed
from src.ui.emojis import NUMBER_EMOJIS
from src.ui.error_view import ErrorView
from src.ui.poll import Poll


class PollView(ErrorView):
    def __init__(self, poll: Poll, embed: PollEmbed, db_poll: aiomysql.pool.Pool):
        super().__init__(timeout=None)
        self.poll = poll
        self.embed = embed
        self.db_poll = db_poll
        self.add_buttons()
        self.add_option_button()

    def add_buttons(self):
        for index, option in enumerate(self.poll.options):
            button = ButtonBackend(
                custom_id=f"{index}:{self.poll.message_id}",
                label=f"{option}",
                emoji=NUMBER_EMOJIS[index],
                poll=self.poll,
                embed=self.embed,
                index=index,
                db_poll=self.db_poll,
            )

            self.add_item(button)

    def add_option_button(self):
        button = NewOptionButton(self.embed, self.poll, self.db_poll)
        self.add_item(button)
