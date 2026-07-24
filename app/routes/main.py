"""Dashboard routes and health checks."""

from flask import Blueprint, redirect, render_template, url_for

from app.auth import get_current_user, login_required, scheduler_required
from services import db

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
@login_required
def index():
    if get_current_user()["role"] == "scheduler":
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("professor_timetable.my_timetable"))


@main_bp.get("/dashboard")
@scheduler_required
def dashboard():
    metrics = db.select_one(
        """
        SELECT
            (SELECT COUNT(*) FROM dbo.professors WHERE is_active = 1) AS professor_count,
            (SELECT COUNT(*) FROM dbo.courses WHERE is_active = 1) AS course_count,
            (SELECT COUNT(*) FROM dbo.rooms WHERE is_active = 1) AS room_count,
            (SELECT COUNT(*) FROM dbo.terms WHERE is_active = 1) AS term_count,
            (SELECT COUNT(*) FROM dbo.lectures WHERE is_active = 1) AS lecture_count
        """
    )
    activity = db.select(
        """
        SELECT TOP 10
            a.entity_type, a.entity_id, a.action, a.created_at,
            u.username AS actor_username
        FROM dbo.activity_log AS a
        LEFT JOIN dbo.users AS u ON u.id = a.actor_user_id
        WHERE a.is_active = 1
        ORDER BY a.created_at DESC, a.id DESC
        """
    )
    return render_template("main/index.html", metrics=metrics, activity=activity)


@main_bp.get("/health")
def health():
    return {"status": "ok"}
