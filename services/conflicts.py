"""Conflict queries for recurring fixed-period allocations."""

from services import db
from services.recurrence import generate_recurring_dates


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


def _find_recurring_conflict(resource_column, resource_id, term_id, period_id, weekdays, exclude_lecture_id=None):
    """Compare proposed dated instances with every existing dated instance."""
    if not weekdays:
        return None

    term = db.select_one(
        "SELECT start_date, end_date FROM dbo.terms WHERE id = %s",
        (term_id,),
    )
    if term is None:
        return None
    proposed_dates = set(generate_recurring_dates(term["start_date"], term["end_date"], weekdays))

    exclude_clause = "" if exclude_lecture_id is None else "AND l.id <> %s"
    params = [term_id, period_id, resource_id]
    if exclude_lecture_id is not None:
        params.append(exclude_lecture_id)
    rows = db.select(
        f"""
        SELECT l.id, l.{resource_column} AS resource_id,
               t.start_date, t.end_date, ld.day_of_week,
               r.room_code, p.first_name, p.last_name
        FROM dbo.lectures AS l
        INNER JOIN dbo.terms AS t ON t.id = l.term_id
        INNER JOIN dbo.lecture_days AS ld ON ld.lecture_id = l.id AND ld.is_active = 1
        INNER JOIN dbo.rooms AS r ON r.id = l.room_id
        INNER JOIN dbo.professors AS p ON p.id = l.professor_id
        WHERE l.is_active = 1
          AND l.term_id = %s
          AND l.period_id = %s
          AND l.{resource_column} = %s
          {exclude_clause}
        ORDER BY l.id, ld.day_of_week
        """,
        tuple(params),
    )

    grouped = {}
    for row in rows:
        lecture = grouped.setdefault(row["id"], {**row, "weekdays": []})
        lecture["weekdays"].append(row["day_of_week"])

    for lecture in grouped.values():
        existing_dates = set(
            generate_recurring_dates(
                lecture["start_date"], lecture["end_date"], lecture["weekdays"]
            )
        )
        overlap = proposed_dates.intersection(existing_dates)
        if overlap:
            lecture["conflict_date"] = min(overlap)
            return lecture
    return None


def find_recurring_room_conflict(term_id, room_id, period_id, weekdays, exclude_lecture_id=None):
    """Find a room collision on any generated date in the term."""
    return _find_recurring_conflict(
        "room_id", room_id, term_id, period_id, weekdays, exclude_lecture_id
    )


def find_recurring_professor_conflict(term_id, professor_id, period_id, weekdays, exclude_lecture_id=None):
    """Find a professor collision on any generated date in the term."""
    return _find_recurring_conflict(
        "professor_id", professor_id, term_id, period_id, weekdays, exclude_lecture_id
    )
