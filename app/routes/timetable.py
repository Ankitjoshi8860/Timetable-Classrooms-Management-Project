"""Scheduler/Admin weekly timetable grid."""

from flask import Blueprint, render_template, request

from app.auth import scheduler_required
from services import db


timetable_bp = Blueprint("timetable", __name__, url_prefix="/timetable")
WEEKDAYS = ((1, "Monday"), (2, "Tuesday"), (3, "Wednesday"), (4, "Thursday"), (5, "Friday"), (6, "Saturday"), (7, "Sunday"))


def _optional_id(name):
    value = request.args.get(name, "").strip()
    return int(value) if value.isdigit() else None


@timetable_bp.get("")
@scheduler_required
def grid():
    terms = db.select(
        "SELECT id, term_name, start_date, end_date FROM dbo.terms WHERE is_active = 1 ORDER BY start_date DESC"
    )
    rooms = db.select("SELECT id, room_code, room_name FROM dbo.rooms WHERE is_active = 1 ORDER BY room_code")
    professors = db.select(
        "SELECT id, first_name, last_name FROM dbo.professors WHERE is_active = 1 ORDER BY last_name, first_name"
    )
    requested_term_id = _optional_id("term_id")
    term_ids = {term["id"] for term in terms}
    term_id = requested_term_id if requested_term_id in term_ids else (terms[0]["id"] if terms else None)
    room_id = _optional_id("room_id")
    professor_id = _optional_id("professor_id")

    periods = db.select(
        "SELECT id, period_number, period_label FROM dbo.periods WHERE is_active = 1 ORDER BY period_number"
    )
    cells = {}
    if term_id is not None:
        filters = ["l.term_id = %s", "l.is_active = 1"]
        params = [term_id]
        if room_id is not None:
            filters.append("l.room_id = %s")
            params.append(room_id)
        if professor_id is not None:
            filters.append("l.professor_id = %s")
            params.append(professor_id)
        lectures = db.select(
            f"""
            SELECT l.id, l.period_id, ld.day_of_week,
                   c.course_code, c.course_name,
                   p.first_name, p.last_name,
                   r.room_code
            FROM dbo.lectures AS l
            INNER JOIN dbo.lecture_days AS ld ON ld.lecture_id = l.id AND ld.is_active = 1
            INNER JOIN dbo.courses AS c ON c.id = l.course_id
            INNER JOIN dbo.professors AS p ON p.id = l.professor_id
            INNER JOIN dbo.rooms AS r ON r.id = l.room_id
            WHERE {' AND '.join(filters)}
            ORDER BY l.period_id, ld.day_of_week, c.course_code
            """,
            tuple(params),
        )
        for lecture in lectures:
            cells.setdefault((lecture["period_id"], lecture["day_of_week"]), []).append(lecture)

    return render_template(
        "timetable/grid.html",
        terms=terms,
        rooms=rooms,
        professors=professors,
        periods=periods,
        cells=cells,
        weekdays=WEEKDAYS,
        selected_term_id=term_id,
        selected_room_id=room_id,
        selected_professor_id=professor_id,
    )
