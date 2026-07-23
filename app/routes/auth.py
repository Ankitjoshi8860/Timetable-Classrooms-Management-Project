"""Login and logout routes."""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from services import db


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = db.select_one(
            """
            SELECT u.id, u.username, u.email, u.password_hash, u.role,
                   p.id AS professor_id
            FROM dbo.users AS u
            LEFT JOIN dbo.professors AS p ON p.user_id = u.id AND p.is_active = 1
            WHERE (u.username = %s OR u.email = %s) AND u.is_active = 1
            """,
            (identifier, identifier),
        )

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username/email or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = True
            return redirect(url_for("main.index"))

    return render_template("auth/login.html")


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
