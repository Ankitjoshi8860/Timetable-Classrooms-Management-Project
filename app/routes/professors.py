"""Scheduler/Admin CRUD routes for professors."""

import json

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from app.auth import scheduler_required
from app.auth import get_current_user
from services import db
from services.activity import log_event


professors_bp = Blueprint("professors", __name__, url_prefix="/professors")


def _values_from_form():
    return {
        "employee_code": request.form.get("employee_code", "").strip(),
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "email": request.form.get("email", "").strip() or None,
    }


def _validate(values, professor_id=None):
    missing = [field.replace("_", " ") for field in ("employee_code", "first_name", "last_name") if not values[field]]
    if missing:
        return f"Please provide: {', '.join(missing)}."

    if professor_id is None:
        duplicate = db.select_one(
            "SELECT id FROM dbo.professors WHERE employee_code = %s",
            (values["employee_code"],),
        )
    else:
        duplicate = db.select_one(
            "SELECT id FROM dbo.professors WHERE employee_code = %s AND id <> %s",
            (values["employee_code"], professor_id),
        )
    if duplicate:
        return "That employee code is already in use."
    return None


def _snapshot(professor):
    return json.dumps(
        {
            "employee_code": professor["employee_code"],
            "first_name": professor["first_name"],
            "last_name": professor["last_name"],
            "email": professor.get("email"),
        },
        sort_keys=True,
    )


@professors_bp.get("")
@scheduler_required
def list_professors():
    professors = db.select(
        """
        SELECT id, employee_code, first_name, last_name, email, is_active,
               created_at, updated_at
        FROM dbo.professors
        ORDER BY is_active DESC, last_name, first_name
        """
    )
    return render_template("professors/list.html", professors=professors)


@professors_bp.get("/<int:professor_id>")
@scheduler_required
def get_professor(professor_id):
    professor = db.select_one(
        """
        SELECT id, employee_code, first_name, last_name, email, is_active,
               created_at, updated_at
        FROM dbo.professors
        WHERE id = %s
        """,
        (professor_id,),
    )
    if professor is None:
        abort(404)
    return jsonify(professor)


@professors_bp.post("/save")
@scheduler_required
def save_professor():
    values = _values_from_form()
    raw_id = request.form.get("id", "").strip()
    professor_id = int(raw_id) if raw_id.isdigit() else None
    error = _validate(values, professor_id)
    if error:
        flash(error, "error")
        return redirect(url_for("professors.list_professors"))

    actor_id = get_current_user()["id"]
    if professor_id is None:
        created = db.insert(
            "dbo.professors",
            {**values, "created_by": actor_id, "updated_by": actor_id},
        )
        log_event(
            entity_type="professor",
            entity_id=created["id"],
            action="create",
            actor_user_id=actor_id,
            new_value=_snapshot(created),
        )
        flash("Professor created.", "success")
    else:
        existing = db.select_one("SELECT * FROM dbo.professors WHERE id = %s", (professor_id,))
        if existing is None:
            abort(404)
        db.update(
            "dbo.professors",
            {**values, "updated_by": actor_id},
            "id = %s",
            (professor_id,),
        )
        log_event(
            entity_type="professor",
            entity_id=professor_id,
            action="update",
            actor_user_id=actor_id,
            old_value=_snapshot(existing),
            new_value=_snapshot({**existing, **values}),
        )
        flash("Professor updated.", "success")
    return redirect(url_for("professors.list_professors"))


@professors_bp.post("/<int:professor_id>/toggle-active")
@scheduler_required
def toggle_active(professor_id):
    professor = db.select_one("SELECT * FROM dbo.professors WHERE id = %s", (professor_id,))
    if professor is None:
        abort(404)

    actor_id = get_current_user()["id"]
    next_active = not bool(professor["is_active"])
    db.update(
        "dbo.professors",
        {"is_active": next_active, "updated_by": actor_id},
        "id = %s",
        (professor_id,),
    )
    log_event(
        entity_type="professor",
        entity_id=professor_id,
        action="restore" if next_active else "deactivate",
        actor_user_id=actor_id,
        old_value=json.dumps({"is_active": bool(professor["is_active"])}),
        new_value=json.dumps({"is_active": next_active}),
    )
    flash("Professor restored." if next_active else "Professor deactivated.", "success")
    return redirect(url_for("professors.list_professors"))
