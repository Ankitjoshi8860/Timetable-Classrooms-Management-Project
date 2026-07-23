"""Scheduler/Admin CRUD routes for rooms."""

import json

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from app.auth import get_current_user, scheduler_required
from services import db
from services.activity import log_event


rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")


def _values_from_form():
    return {
        "room_code": request.form.get("room_code", "").strip(),
        "room_name": request.form.get("room_name", "").strip(),
        "building": request.form.get("building", "").strip(),
    }


def _validate(values, room_id=None):
    missing = [field.replace("_", " ") for field in ("room_code", "room_name", "building") if not values[field]]
    if missing:
        return f"Please provide: {', '.join(missing)}."

    if room_id is None:
        duplicate = db.select_one("SELECT id FROM dbo.rooms WHERE room_code = %s", (values["room_code"],))
    else:
        duplicate = db.select_one(
            "SELECT id FROM dbo.rooms WHERE room_code = %s AND id <> %s",
            (values["room_code"], room_id),
        )
    if duplicate:
        return "That room number/code is already in use."
    return None


def _snapshot(room):
    return json.dumps(
        {
            "room_code": room["room_code"],
            "room_name": room["room_name"],
            "building": room["building"],
        },
        sort_keys=True,
    )


@rooms_bp.get("")
@scheduler_required
def list_rooms():
    rooms = db.select(
        """
        SELECT id, room_code, room_name, building, is_active, created_at, updated_at
        FROM dbo.rooms
        ORDER BY is_active DESC, building, room_code
        """
    )
    return render_template("rooms/list.html", rooms=rooms)


@rooms_bp.get("/<int:room_id>")
@scheduler_required
def get_room(room_id):
    room = db.select_one(
        """
        SELECT id, room_code, room_name, building, is_active, created_at, updated_at
        FROM dbo.rooms
        WHERE id = %s
        """,
        (room_id,),
    )
    if room is None:
        abort(404)
    return jsonify(room)


@rooms_bp.post("/save")
@scheduler_required
def save_room():
    values = _values_from_form()
    raw_id = request.form.get("id", "").strip()
    room_id = int(raw_id) if raw_id.isdigit() else None
    error = _validate(values, room_id)
    if error:
        flash(error, "error")
        return redirect(url_for("rooms.list_rooms"))

    actor_id = get_current_user()["id"]
    if room_id is None:
        created = db.insert("dbo.rooms", {**values, "created_by": actor_id, "updated_by": actor_id})
        log_event(
            entity_type="room",
            entity_id=created["id"],
            action="create",
            actor_user_id=actor_id,
            new_value=_snapshot(created),
        )
        flash("Room created.", "success")
    else:
        existing = db.select_one("SELECT * FROM dbo.rooms WHERE id = %s", (room_id,))
        if existing is None:
            abort(404)
        db.update("dbo.rooms", {**values, "updated_by": actor_id}, "id = %s", (room_id,))
        log_event(
            entity_type="room",
            entity_id=room_id,
            action="update",
            actor_user_id=actor_id,
            old_value=_snapshot(existing),
            new_value=_snapshot({**existing, **values}),
        )
        flash("Room updated.", "success")
    return redirect(url_for("rooms.list_rooms"))


@rooms_bp.post("/<int:room_id>/toggle-active")
@scheduler_required
def toggle_active(room_id):
    room = db.select_one("SELECT * FROM dbo.rooms WHERE id = %s", (room_id,))
    if room is None:
        abort(404)

    actor_id = get_current_user()["id"]
    next_active = not bool(room["is_active"])
    db.update("dbo.rooms", {"is_active": next_active, "updated_by": actor_id}, "id = %s", (room_id,))
    log_event(
        entity_type="room",
        entity_id=room_id,
        action="restore" if next_active else "deactivate",
        actor_user_id=actor_id,
        old_value=json.dumps({"is_active": bool(room["is_active"])}),
        new_value=json.dumps({"is_active": next_active}),
    )
    flash("Room restored." if next_active else "Room deactivated.", "success")
    return redirect(url_for("rooms.list_rooms"))
