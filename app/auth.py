"""Authentication helpers and server-side permission guards."""

from functools import wraps

from flask import abort, g, redirect, session, url_for

from services import db


def get_current_user():
    """Return the active user for the request, or ``None`` when anonymous."""
    if "user_id" not in session:
        return None

    if "current_user" not in g:
        g.current_user = db.select_one(
            """
            SELECT u.id, u.username, u.email, u.role, p.id AS professor_id
            FROM dbo.users AS u
            LEFT JOIN dbo.professors AS p ON p.user_id = u.id AND p.is_active = 1
            WHERE u.id = %s AND u.is_active = 1
            """,
            (session["user_id"],),
        )
        if g.current_user is None:
            session.clear()

    return g.current_user


def login_required(view):
    """Require an active authenticated user before entering a view."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def roles_required(*roles):
    """Require an authenticated user with one of the supplied roles."""
    allowed_roles = set(roles)

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return redirect(url_for("auth.login"))
            if user["role"] not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def scheduler_required(view):
    """Restrict a view to Scheduler/Admin users."""
    return roles_required("scheduler")(view)


def professor_required(view):
    """Restrict a view to Professor users."""
    return roles_required("professor")(view)
