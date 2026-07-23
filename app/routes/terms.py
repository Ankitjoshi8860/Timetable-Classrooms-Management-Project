"""Scheduler/Admin CRUD routes for academic terms."""

import json
from datetime import date

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from app.auth import get_current_user, scheduler_required
from services import db
from services.activity import log_event


terms_bp = Blueprint("terms", __name__, url_prefix="/terms")


def _values_from_form():
    return {
        "term_name": request.form.get("term_name", "").strip(),
        "start_date": request.form.get("start_date", "").strip(),
        "end_date": request.form.get("end_date", "").strip(),
    }


def _validate(values, term_id=None):
    missing = [field.replace("_", " ") for field in ("term_name", "start_date", "end_date") if not values[field]]
    if missing:
        return f"Please provide: {', '.join(missing)}."
    try:
        start = date.fromisoformat(values["start_date"])
        end = date.fromisoformat(values["end_date"])
    except ValueError:
        return "Start and end dates must be valid calendar dates."
    if end < start:
        return "The end date cannot be before the start date."

    if term_id is None:
        duplicate = db.select_one(
            "SELECT id FROM dbo.terms WHERE term_name = %s AND start_date = %s",
            (values["term_name"], values["start_date"]),
        )
    else:
        duplicate = db.select_one(
            "SELECT id FROM dbo.terms WHERE term_name = %s AND start_date = %s AND id <> %s",
            (values["term_name"], values["start_date"], term_id),
        )
    if duplicate:
        return "A term with that name and start date already exists."
    return None


def _snapshot(term):
    return json.dumps(
        {
            "term_name": term["term_name"],
            "start_date": str(term["start_date"]),
            "end_date": str(term["end_date"]),
        },
        sort_keys=True,
    )


@terms_bp.get("")
@scheduler_required
def list_terms():
    terms = db.select(
        """
        SELECT id, term_name, start_date, end_date, is_active, created_at, updated_at
        FROM dbo.terms
        ORDER BY is_active DESC, start_date DESC, term_name
        """
    )
    return render_template("terms/list.html", terms=terms)


@terms_bp.get("/<int:term_id>")
@scheduler_required
def get_term(term_id):
    term = db.select_one(
        """
        SELECT id, term_name, start_date, end_date, is_active, created_at, updated_at
        FROM dbo.terms
        WHERE id = %s
        """,
        (term_id,),
    )
    if term is None:
        abort(404)
    return jsonify(term)


@terms_bp.post("/save")
@scheduler_required
def save_term():
    values = _values_from_form()
    raw_id = request.form.get("id", "").strip()
    term_id = int(raw_id) if raw_id.isdigit() else None
    error = _validate(values, term_id)
    if error:
        flash(error, "error")
        return redirect(url_for("terms.list_terms"))

    actor_id = get_current_user()["id"]
    if term_id is None:
        created = db.insert("dbo.terms", {**values, "created_by": actor_id, "updated_by": actor_id})
        log_event(
            entity_type="term",
            entity_id=created["id"],
            action="create",
            actor_user_id=actor_id,
            new_value=_snapshot(created),
        )
        flash("Term created.", "success")
    else:
        existing = db.select_one("SELECT * FROM dbo.terms WHERE id = %s", (term_id,))
        if existing is None:
            abort(404)
        db.update("dbo.terms", {**values, "updated_by": actor_id}, "id = %s", (term_id,))
        log_event(
            entity_type="term",
            entity_id=term_id,
            action="update",
            actor_user_id=actor_id,
            old_value=_snapshot(existing),
            new_value=_snapshot({**existing, **values}),
        )
        flash("Term updated.", "success")
    return redirect(url_for("terms.list_terms"))


@terms_bp.post("/<int:term_id>/toggle-active")
@scheduler_required
def toggle_active(term_id):
    term = db.select_one("SELECT * FROM dbo.terms WHERE id = %s", (term_id,))
    if term is None:
        abort(404)

    actor_id = get_current_user()["id"]
    next_active = not bool(term["is_active"])
    db.update("dbo.terms", {"is_active": next_active, "updated_by": actor_id}, "id = %s", (term_id,))
    log_event(
        entity_type="term",
        entity_id=term_id,
        action="restore" if next_active else "deactivate",
        actor_user_id=actor_id,
        old_value=json.dumps({"is_active": bool(term["is_active"])}),
        new_value=json.dumps({"is_active": next_active}),
    )
    flash("Term restored." if next_active else "Term deactivated.", "success")
    return redirect(url_for("terms.list_terms"))
