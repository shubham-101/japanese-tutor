from datetime import datetime, timedelta


def calculate_next_review(
    mastery: int,
    correct: bool,
) -> tuple[int, datetime]:

    now = datetime.utcnow()

    if not correct:
        mastery = max(0, mastery - 1)

        return mastery, now + timedelta(
            minutes=10
        )

    mastery += 1

    intervals = {
        1: 1,
        2: 3,
        3: 7,
        4: 14,
        5: 30,
        6: 60,
        7: 120,
        8: 240,
    }

    days = intervals.get(
        mastery,
        240,
    )

    return mastery, now + timedelta(
        days=days
    )