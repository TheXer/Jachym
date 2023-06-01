from datetime import datetime, timedelta

"""
I'd like to test using the pytest, unfortunately I have to use manual testing through discord to check the correct
behaviour of the bot. This is to ease the writing of tests, as I can generate them and use them for testing.
"""


def test_pools(count=2) -> str:
    test_str = '!anketa "Test"'

    if 10 >= count >= 2:
        for x in range(count):
            test_str += f' "Question no. {x}"'

    return test_str


def test_events():
    date = datetime.now() + timedelta(minutes=1)
    test_string = (
        f'!udalost create "Name" "Description" "{date.strftime("%d.%m.%Y %H:%M")}"'
    )

    return test_string


print(test_pools(5))
print(test_events())
