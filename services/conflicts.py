"""Conflict queries for recurring fixed-period allocations."""

from services import db


def _weekday_placeholders(weekdays):
    return ", ".join("%s" for _ in weekdays)


def find_room_conflict(term_id, room_id, period_id, weekdays, exclude_lecture_id=None):
    """Return an existing lecture using the same room/day/period in a term."""
    if not weekdays:
        return None
    exclude_clause = "" if exclude_lecture_id is None else "AND l.id <> %s"
    params = [term_id, room_id, period_id, *weekdays]
    if exclude_lecture_id is not None:
        params.append(exclude_lecture_id)
    return db.select_one(
        f"""
        SELECT TOP 1 l.id, l.room_id, r.room_code, ld.day_of_week
        FROM dbo.lectures AS l
        INNER JOIN dbo.lecture_days AS ld ON ld.lecture_id = l.id AND ld.is_active = 1
        INNER JOIN dbo.rooms AS r ON r.id = l.room_id
        WHERE l.is_active = 1
          AND l.term_id = %s
          AND l.room_id = %s
          AND l.period_id = %s
          AND ld.day_of_week IN ({_weekday_placeholders(weekdays)})
          {exclude_clause}
        ORDER BY l.id
        """,
        tuple(params),
    )


def find_professor_conflict(term_id, professor_id, period_id, weekdays, exclude_lecture_id=None):
    """Return an existing lecture using the same professor/day/period in a term."""
    if not weekdays:
        return None
    exclude_clause = "" if exclude_lecture_id is None else "AND l.id <> %s"
    params = [term_id, professor_id, period_id, *weekdays]
    if exclude_lecture_id is not None:
        params.append(exclude_lecture_id)
    return db.select_one(
        f"""
        SELECT TOP 1 l.id, l.professor_id, p.first_name, p.last_name, ld.day_of_week
        FROM dbo.lectures AS l
        INNER JOIN dbo.lecture_days AS ld ON ld.lecture_id = l.id AND ld.is_active = 1
        INNER JOIN dbo.professors AS p ON p.id = l.professor_id
        WHERE l.is_active = 1
          AND l.term_id = %s
          AND l.professor_id = %s
          AND l.period_id = %s
          AND ld.day_of_week IN ({_weekday_placeholders(weekdays)})
          {exclude_clause}
        ORDER BY l.id
        """,
        tuple(params),
    )
