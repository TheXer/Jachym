import datetime

import pytest

from src.ui.poll import Poll

MESSAGE_ID = 123456789
CHANNEL_ID = 123456789
QUESTION = "Test No. 1"
OPTIONS = ["1", "2", "3"]
USER_ID = 123456789


@pytest.mark.parametrize(
    "date_test",
    [
        datetime.datetime.now(),
        datetime.date.today(),
        datetime.datetime.now().strftime("%Y-%m-%d"),
    ],
)
def test_datetime(date_test):
    pool = Poll(MESSAGE_ID, CHANNEL_ID, QUESTION, OPTIONS, USER_ID, date_test)
    assert pool.created_at == datetime.date.today()
