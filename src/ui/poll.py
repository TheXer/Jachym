from datetime import datetime
from typing import Optional


class Poll:
    MAX_OPTIONS = 10
    MIN_OPTIONS = 2

    __slots__ = [
        "_message_id",
        "_channel_id",
        "_question",
        "_options",
        "_date_created_at",
        "_user_id"
    ]

    def __init__(
            self,
            message_id: int,
            channel_id: int,
            question: str,
            options: tuple[str, ...],
            user_id: Optional[int] = None,
            date_created: Optional[datetime] = datetime.now().strftime("%Y-%m-%d")
    ):
        self._message_id = message_id
        self._channel_id = channel_id
        self._question = question
        self._options = options
        self._date_created_at = date_created
        self._user_id = user_id

    @property
    def message_id(self) -> int:
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
    def created_at(self) -> datetime.date:
        if isinstance(self._date_created_at, str):
            return datetime.fromisoformat(self._date_created_at).date()
        return self._date_created_at

    @property
    def user_id(self) -> int:
        return self._user_id
