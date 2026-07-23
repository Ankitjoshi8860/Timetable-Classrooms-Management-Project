"""Scheduler/Admin CRUD routes for courses."""

import json

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from app.auth import get_current_user, scheduler_required
from services import db
from services.activity import log_event


courses_bp = Blueprint("courses", __name__, url_prefix="/courses")


def _values_from_form():
    raw_credit_hours = request.form.get("credit_hours", "").strip()
    return {
        "course_code": request.form.get("course_code", "").strip(),
        "course_name": request.form.get("course_name", "").strip(),
        "department": request.form.get("department", "").strip(),
        "credit_hours": int(raw_credit_hours) if raw_credit_hours.isdigit() else None,
        "description": request.form.get("description", "").strip() or None,
    }


def _validate(values, course_id=None):
    required = ("course_code", "course_name", "department")
    missing = [field.replace("_", " ") for field in required if not values[field]]
    if missing:
        return f"Please provide: {', '.join(missing)}."
    if values["credit_hours"] is None or not 1 <= values["credit_hours"] <= 12:
        return "Credit hours must be a whole number between 1 and 12."

    if course_id is None:
        duplicate = db.select_one("SELECT id FROM dbo.courses WHERE course_code = %s", (values["course_code"],))
    else:
        duplicate = db.select_one(
            "SELECT id FROM dbo.courses WHERE course_code = %s AND id <> %s",
            (values["course_code"], course_id),
        )
    if duplicate:
        return "That course code is already in use."
    return None


def _snapshot(course):
    return json.dumps(
        {
            "course_code": course["course_code"],
            "course_name": course["course_name"],
            "department": course["department"],
            "credit_hours": course["credit_hours"],
            "description": course.get("description"),
        },
        sort_keys=True,
    )


@courses_bp.get("")
@scheduler_required
def list_courses():
    courses = db.select(
        """
        SELECT id, course_code, course_name, department, credit_hours,
               description, is_active, created_at, updated_at
        FROM dbo.courses
        ORDER BY is_active DESC, course_code
        """
    )
    return render_template("courses/list.html", courses=courses)


@courses_bp.get("/<int:course_id>")
@scheduler_required
def get_course(course_id):
    course = db.select_one(
        """
        SELECT id, course_code, course_name, department, credit_hours,
               description, is_active, created_at, updated_at
        FROM dbo.courses
        WHERE id = %s
        """,
        (course_id,),
    )
    if course is None:
        abort(404)
    return jsonify(course)


@courses_bp.post("/save")
@scheduler_required
def save_course():
    values = _values_from_form()
    raw_id = request.form.get("id", "").strip()
    course_id = int(raw_id) if raw_id.isdigit() else None
    error = _validate(values, course_id)
    if error:
        flash(error, "error")
        return redirect(url_for("courses.list_courses"))

    actor_id = get_current_user()["id"]
    if course_id is None:
        created = db.insert(
            "dbo.courses",
            {**values, "created_by": actor_id, "updated_by": actor_id},
        )
        log_event(
            entity_type="course",
            entity_id=created["id"],
            action="create",
            actor_user_id=actor_id,
            new_value=_snapshot(created),
        )
        flash("Course created.", "success")
    else:
        existing = db.select_one("SELECT * FROM dbo.courses WHERE id = %s", (course_id,))
        if existing is None:
            abort(404)
        db.update("dbo.courses", {**values, "updated_by": actor_id}, "id = %s", (course_id,))
        log_event(
            entity_type="course",
            entity_id=course_id,
            action="update",
            actor_user_id=actor_id,
            old_value=_snapshot(existing),
            new_value=_snapshot({**existing, **values}),
        )
        flash("Course updated.", "success")
    return redirect(url_for("courses.list_courses"))


@courses_bp.post("/<int:course_id>/toggle-active")
@scheduler_required
def toggle_active(course_id):
    course = db.select_one("SELECT * FROM dbo.courses WHERE id = %s", (course_id,))
    if course is None:
        abort(404)

    actor_id = get_current_user()["id"]
    next_active = not bool(course["is_active"])
    db.update("dbo.courses", {"is_active": next_active, "updated_by": actor_id}, "id = %s", (course_id,))
    log_event(
        entity_type="course",
        entity_id=course_id,
        action="restore" if next_active else "deactivate",
        actor_user_id=actor_id,
        old_value=json.dumps({"is_active": bool(course["is_active"])}),
        new_value=json.dumps({"is_active": next_active}),
    )
    flash("Course restored." if next_active else "Course deactivated.", "success")
    return redirect(url_for("courses.list_courses"))
