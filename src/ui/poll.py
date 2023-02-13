from datetime import datetime
from typing import Optional

from discord import Message


class Poll:
    MAX_OPTIONS = 10
    MIN_OPTIONS = 2

    def __init__(
            self,
            message_id: int,
            channel_id: int,
            question: str,
            options: tuple[str, ...],
            user_id: Optional[int] = None
    ):
        self._message_id = message_id
        self._channel_id = channel_id
        self._question = question
        self._options = options
        self._date_created_at = datetime.now().strftime("%Y-%m-%d")
        self._user_id = user_id

    @property
    def message_id(self):
        return self._message_id

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def question(self) -> str:
        return self._question

    @property
    def options(self) -> tuple[str, ...]:
        return self._options

    @property
    def created_at(self) -> str:
        return self._date_created_at

    @property
    def user_id(self) -> int:
        return self._user_id

    @classmethod
    async def create_poll(cls, message: Message, question: str, *answers) -> "Poll":
        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answers)

        return poll
