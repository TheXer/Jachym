from datetime import datetime
from typing import Optional

from discord import Message


class Poll:
    MAX_OPTIONS = 10
    MIN_OPTIONS = 2

    def __init__(
            self,
            message_id: Message.id,
            channel_id: int,
            question: str,
            options: tuple[str, ...],
            user_id: Optional[int] = None
    ):
        self.message_id = message_id
        self.channel_id = channel_id
        self.question = question
        self.options = options
        self.date_created_at = datetime.now().strftime("%Y-%m-%d")
        self.user_id = user_id

    def message_id(self) -> int:
        return self.message_id

    def channel_id(self) -> int:
        return self.channel_id

    def question(self) -> str:
        return self.question

    def options(self) -> tuple[str, ...]:
        return self.options

    def created_at(self) -> str:
        return self.date_created_at

    def user_id(self) -> int:
        return self.user_id

    def delete(self):
        # connection to database, make new tables and view
        pass

    @classmethod
    async def create_poll(cls, message: Message, question: str, *answers) -> "Poll":
        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answers)

        return poll
