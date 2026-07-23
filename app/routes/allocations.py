"""Scheduler/Admin lecture allocation routes."""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth import get_current_user, scheduler_required
from services.conflicts import find_recurring_professor_conflict, find_recurring_room_conflict
from services import db
from services.activity import log_event


allocations_bp = Blueprint("allocations", __name__, url_prefix="/allocations")


def _active_options():
    return {
        "courses": db.select(
            "SELECT id, course_code, course_name FROM dbo.courses WHERE is_active = 1 ORDER BY course_code"
        ),
        "professors": db.select(
            "SELECT id, employee_code, first_name, last_name FROM dbo.professors WHERE is_active = 1 ORDER BY last_name, first_name"
        ),
        "rooms": db.select(
            "SELECT id, room_code, room_name, building FROM dbo.rooms WHERE is_active = 1 ORDER BY building, room_code"
        ),
        "terms": db.select(
            "SELECT id, term_name, start_date, end_date FROM dbo.terms WHERE is_active = 1 ORDER BY start_date DESC"
        ),
        "periods": db.select(
            "SELECT id, period_number, period_label FROM dbo.periods WHERE is_active = 1 ORDER BY period_number"
        ),
    }


def _selected_ids():
    values = {}
    for name in ("course_id", "professor_id", "room_id", "term_id", "period_id"):
        raw_value = request.form.get(name, "").strip()
        values[name] = int(raw_value) if raw_value.isdigit() else None
    days = []
    for raw_day in request.form.getlist("days"):
        if raw_day.isdigit() and 1 <= int(raw_day) <= 7:
            days.append(int(raw_day))
    values["days"] = sorted(set(days))
    return values


def _validate_active_selection(values):
    required = ("course_id", "professor_id", "room_id", "term_id", "period_id")
    if any(values[field] is None for field in required):
        return "Select a course, professor, room, term, and fixed period."
    if not values["days"]:
        return "Select at least one recurring weekday."

    checks = (
        ("course_id", "courses"),
        ("professor_id", "professors"),
        ("room_id", "rooms"),
        ("term_id", "terms"),
        ("period_id", "periods"),
    )
    for field, table in checks:
        if db.select_one(f"SELECT id FROM dbo.{table} WHERE id = %s AND is_active = 1", (values[field],)) is None:
            return "Only active courses, professors, rooms, terms, and periods can be allocated."
    return None


@allocations_bp.route("/new", methods=("GET", "POST"))
@scheduler_required
def new_allocation():
    if request.method == "POST":
        values = _selected_ids()
        error = _validate_active_selection(values)
        if error:
            flash(error, "error")
            return redirect(url_for("allocations.new_allocation"))

        room_conflict = find_recurring_room_conflict(
            values["term_id"], values["room_id"], values["period_id"], values["days"]
        )
        if room_conflict:
            flash(
                f"Room {room_conflict['room_code']} is already booked for one of the selected weekdays and this period.",
                "error",
            )
            return redirect(url_for("allocations.new_allocation"))

        professor_conflict = find_recurring_professor_conflict(
            values["term_id"], values["professor_id"], values["period_id"], values["days"]
        )
        if professor_conflict:
            flash(
                f"Professor {professor_conflict['first_name']} {professor_conflict['last_name']} is already scheduled for one of the selected weekdays and this period.",
                "error",
            )
            return redirect(url_for("allocations.new_allocation"))

        actor_id = get_current_user()["id"]
        with db.begin_transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.lectures
                    (course_id, professor_id, room_id, term_id, period_id, created_by, updated_by)
                OUTPUT INSERTED.id
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    values["course_id"], values["professor_id"], values["room_id"],
                    values["term_id"], values["period_id"], actor_id, actor_id,
                ),
            )
            lecture_id = cursor.fetchone()["id"]
            for day in values["days"]:
                cursor.execute(
                    """
                    INSERT INTO dbo.lecture_days
                        (lecture_id, day_of_week, created_by, updated_by)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (lecture_id, day, actor_id, actor_id),
                )

        log_event(
            entity_type="lecture",
            entity_id=lecture_id,
            action="create",
            actor_user_id=actor_id,
            new_value=json.dumps({**values, "lecture_id": lecture_id}, sort_keys=True, default=str),
        )
        flash("Lecture allocation created.", "success")
        return redirect(url_for("allocations.new_allocation"))

    return render_template("allocations/new.html", **_active_options())
