"""Read-only personal timetable routes for professor users."""

from flask import Blueprint, abort, render_template, request

from app.auth import get_current_user, professor_required
from services import db


professor_timetable_bp = Blueprint(
    "professor_timetable", __name__, url_prefix="/my-timetable"
)
WEEKDAYS = (
    (1, "Monday"), (2, "Tuesday"), (3, "Wednesday"), (4, "Thursday"),
    (5, "Friday"), (6, "Saturday"), (7, "Sunday"),
)


def _selected_term_id(terms):
    raw_term_id = request.args.get("term_id", "").strip()
    requested_term_id = int(raw_term_id) if raw_term_id.isdigit() else None
    available_term_ids = {term["id"] for term in terms}
    if requested_term_id in available_term_ids:
        return requested_term_id
    return terms[0]["id"] if terms else None


@professor_timetable_bp.get("")
@professor_required
def my_timetable():
    """Show the logged-in professor's lectures without exposing other schedules."""
    professor_id = get_current_user()["professor_id"]
    if professor_id is None:
        abort(403)

    terms = db.select(
        "SELECT id, term_name, start_date, end_date FROM dbo.terms "
        "WHERE is_active = 1 ORDER BY start_date DESC"
    )
    selected_term_id = _selected_term_id(terms)
    periods = db.select(
        "SELECT id, period_number, period_label FROM dbo.periods "
        "WHERE is_active = 1 ORDER BY period_number"
    )
    cells = {}
    if selected_term_id is not None:
        lectures = db.select(
            """
            SELECT l.period_id, ld.day_of_week,
                   c.course_code, c.course_name, r.room_code, r.room_name
            FROM dbo.lectures AS l
            INNER JOIN dbo.lecture_days AS ld
                ON ld.lecture_id = l.id AND ld.is_active = 1
            INNER JOIN dbo.courses AS c ON c.id = l.course_id
            INNER JOIN dbo.rooms AS r ON r.id = l.room_id
            WHERE l.is_active = 1
              AND l.term_id = %s
              AND l.professor_id = %s
            ORDER BY l.period_id, ld.day_of_week, c.course_code
            """,
            (selected_term_id, professor_id),
        )
        for lecture in lectures:
            cells.setdefault((lecture["period_id"], lecture["day_of_week"]), []).append(lecture)

    return render_template(
        "timetable/professor_grid.html",
        terms=terms,
        periods=periods,
        cells=cells,
        weekdays=WEEKDAYS,
        selected_term_id=selected_term_id,
    )
