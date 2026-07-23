"""Routes shared by the application shell and health checks."""

from flask import Blueprint, render_template

from app.auth import login_required

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
@login_required
def index():
    return render_template("main/index.html")


@main_bp.get("/health")
def health():
    return {"status": "ok"}
