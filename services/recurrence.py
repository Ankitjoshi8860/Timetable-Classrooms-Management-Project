"""Term-bounded expansion for fixed-period recurring lectures."""

from datetime import date, timedelta

from services import db


def generate_recurring_dates(start_date, end_date, weekdays):
    """Return every matching weekday between two inclusive term dates.

    Weekdays use the application convention 1=Monday through 7=Sunday.
    The lecture remains one recurring record; these dates are generated only
    when validation or a view needs the dated instances.
    """
    if end_date < start_date:
        raise ValueError("The term end date cannot be before its start date.")
    selected_days = {int(day) for day in weekdays}
    if not selected_days or not selected_days.issubset(set(range(1, 8))):
        raise ValueError("Weekdays must contain one or more values from 1 through 7.")

    first_offset = min((day - 1 - start_date.weekday()) % 7 for day in selected_days)
    current = start_date + timedelta(days=first_offset)
    instances = []
    while current <= end_date:
        if current.isoweekday() in selected_days:
            instances.append(current)
        current += timedelta(days=1)
    return instances


def get_lecture_instances(lecture_id):
    """Load one lecture and expand its recurring weekdays within its term."""
    lecture = db.select_one(
        """
        SELECT l.id AS lecture_id, l.term_id, l.period_id,
               p.period_number, p.period_label, t.start_date, t.end_date
        FROM dbo.lectures AS l
        INNER JOIN dbo.periods AS p ON p.id = l.period_id AND p.is_active = 1
        INNER JOIN dbo.terms AS t ON t.id = l.term_id
        WHERE l.id = %s AND l.is_active = 1
        """,
        (lecture_id,),
    )
    if lecture is None:
        return []

    weekday_rows = db.select(
        """
        SELECT day_of_week
        FROM dbo.lecture_days
        WHERE lecture_id = %s AND is_active = 1
        ORDER BY day_of_week
        """,
        (lecture_id,),
    )
    dates = generate_recurring_dates(
        lecture["start_date"],
        lecture["end_date"],
        [row["day_of_week"] for row in weekday_rows],
    )
    return [
        {
            "lecture_id": lecture["lecture_id"],
            "term_id": lecture["term_id"],
            "date": instance_date,
            "period_id": lecture["period_id"],
            "period_number": lecture["period_number"],
            "period_label": lecture["period_label"],
        }
        for instance_date in dates
    ]
