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


def _lecture_snapshot(lecture):
    return {
        "course_id": lecture["course_id"],
        "professor_id": lecture["professor_id"],
        "room_id": lecture["room_id"],
        "term_id": lecture["term_id"],
        "period_id": lecture["period_id"],
        "days": lecture["days"],
    }


def _get_active_lecture(lecture_id):
    lecture = db.select_one(
        """
        SELECT id, course_id, professor_id, room_id, term_id, period_id
        FROM dbo.lectures
        WHERE id = %s AND is_active = 1
        """,
        (lecture_id,),
    )
    if lecture is None:
        return None
    lecture["days"] = [
        row["day_of_week"]
        for row in db.select(
            """
            SELECT day_of_week
            FROM dbo.lecture_days
            WHERE lecture_id = %s AND is_active = 1
            ORDER BY day_of_week
            """,
            (lecture_id,),
        )
    ]
    return lecture


def _conflict_error(values, exclude_lecture_id=None):
    room_conflict = find_recurring_room_conflict(
        values["term_id"], values["room_id"], values["period_id"], values["days"],
        exclude_lecture_id=exclude_lecture_id,
    )
    if room_conflict:
        return (
            f"Room {room_conflict['room_code']} is already booked for one of the "
            "selected weekdays and this period."
        )

    professor_conflict = find_recurring_professor_conflict(
        values["term_id"], values["professor_id"], values["period_id"], values["days"],
        exclude_lecture_id=exclude_lecture_id,
    )
    if professor_conflict:
        return (
            f"Professor {professor_conflict['first_name']} "
            f"{professor_conflict['last_name']} is already scheduled for one of the "
            "selected weekdays and this period."
        )
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

        error = _conflict_error(values)
        if error:
            flash(error, "error")
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

    return render_template(
        "allocations/form.html",
        lecture=None,
        form_action=url_for("allocations.new_allocation"),
        **_active_options(),
    )


@allocations_bp.route("/<int:lecture_id>/edit", methods=("GET", "POST"))
@scheduler_required
def edit_allocation(lecture_id):
    lecture = _get_active_lecture(lecture_id)
    if lecture is None:
        return ("Lecture allocation not found.", 404)

    if request.method == "POST":
        values = _selected_ids()
        error = _validate_active_selection(values) or _conflict_error(
            values, exclude_lecture_id=lecture_id
        )
        if error:
            flash(error, "error")
            return redirect(url_for("allocations.edit_allocation", lecture_id=lecture_id))

        actor_id = get_current_user()["id"]
        old_value = _lecture_snapshot(lecture)
        with db.begin_transaction() as cursor:
            cursor.execute(
                """
                UPDATE dbo.lectures
                SET course_id = %s, professor_id = %s, room_id = %s,
                    term_id = %s, period_id = %s, updated_by = %s,
                    updated_at = SYSUTCDATETIME()
                WHERE id = %s
                """,
                (
                    values["course_id"], values["professor_id"], values["room_id"],
                    values["term_id"], values["period_id"], actor_id, lecture_id,
                ),
            )
            cursor.execute(
                """
                UPDATE dbo.lecture_days
                SET is_active = 0, updated_by = %s, updated_at = SYSUTCDATETIME()
                WHERE lecture_id = %s AND is_active = 1
                """,
                (actor_id, lecture_id),
            )
            for day in values["days"]:
                cursor.execute(
                    """
                    IF EXISTS (SELECT 1 FROM dbo.lecture_days WHERE lecture_id = %s AND day_of_week = %s)
                        UPDATE dbo.lecture_days
                        SET is_active = 1, updated_by = %s, updated_at = SYSUTCDATETIME()
                        WHERE lecture_id = %s AND day_of_week = %s
                    ELSE
                        INSERT INTO dbo.lecture_days
                            (lecture_id, day_of_week, created_by, updated_by)
                        VALUES (%s, %s, %s, %s)
                    """,
                    (lecture_id, day, actor_id, lecture_id, day, lecture_id, day, actor_id, actor_id),
                )

        log_event(
            entity_type="lecture",
            entity_id=lecture_id,
            action="update",
            actor_user_id=actor_id,
            old_value=json.dumps(old_value, sort_keys=True),
            new_value=json.dumps(values, sort_keys=True),
        )
        flash("Lecture allocation updated.", "success")
        return redirect(url_for("allocations.edit_allocation", lecture_id=lecture_id))

    return render_template(
        "allocations/form.html",
        lecture=lecture,
        form_action=url_for("allocations.edit_allocation", lecture_id=lecture_id),
        **_active_options(),
    )
