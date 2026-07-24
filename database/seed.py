"""Create repeatable local demo data through the shared database wrapper."""

import os

from werkzeug.security import generate_password_hash

from services import db


def _required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing {name}. Set local seed credentials in .env before running the seed."
        )
    return value


def _ensure_user(username, email, password, role):
    existing = db.select_one(
        "SELECT id, username, email, role FROM dbo.users WHERE username = %s OR email = %s",
        (username, email),
    )
    if existing:
        return existing["id"], False

    created = db.insert(
        "dbo.users",
        {
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": role,
        },
    )
    return created["id"], True


def _ensure_professor(data, created_by):
    existing = db.select_one(
        "SELECT id FROM dbo.professors WHERE employee_code = %s",
        (data["employee_code"],),
    )
    if existing:
        return existing["id"], False

    values = {**data, "created_by": created_by, "updated_by": created_by}
    created = db.insert("dbo.professors", values)
    return created["id"], True


def _ensure_course(data, created_by):
    existing = db.select_one(
        "SELECT id FROM dbo.courses WHERE course_code = %s",
        (data["course_code"],),
    )
    if existing:
        return existing["id"], False

    values = {**data, "created_by": created_by, "updated_by": created_by}
    created = db.insert("dbo.courses", values)
    return created["id"], True


def _ensure_room(data, created_by):
    existing = db.select_one(
        "SELECT id FROM dbo.rooms WHERE room_code = %s",
        (data["room_code"],),
    )
    if existing:
        return existing["id"], False

    values = {**data, "created_by": created_by, "updated_by": created_by}
    created = db.insert("dbo.rooms", values)
    return created["id"], True


def _ensure_term(data, created_by):
    existing = db.select_one(
        "SELECT id FROM dbo.terms WHERE term_name = %s AND start_date = %s",
        (data["term_name"], data["start_date"]),
    )
    if existing:
        return existing["id"], False

    values = {**data, "created_by": created_by, "updated_by": created_by}
    created = db.insert("dbo.terms", values)
    return created["id"], True


def _ensure_lecture(data, weekdays, created_by):
    existing = db.select_one(
        """
        SELECT id FROM dbo.lectures
        WHERE course_id = %s AND professor_id = %s AND room_id = %s
          AND term_id = %s AND period_id = %s AND is_active = 1
        """,
        (data["course_id"], data["professor_id"], data["room_id"], data["term_id"], data["period_id"]),
    )
    if existing:
        lecture_id, created = existing["id"], False
    else:
        created_row = db.insert(
            "dbo.lectures",
            {**data, "created_by": created_by, "updated_by": created_by},
        )
        lecture_id, created = created_row["id"], True

    for day in sorted(set(weekdays)):
        day_row = db.select_one(
            "SELECT is_active FROM dbo.lecture_days WHERE lecture_id = %s AND day_of_week = %s",
            (lecture_id, day),
        )
        if day_row is None:
            db.insert(
                "dbo.lecture_days",
                {"lecture_id": lecture_id, "day_of_week": day, "created_by": created_by, "updated_by": created_by},
            )
        elif not day_row["is_active"]:
            db.update(
                "dbo.lecture_days", {"is_active": True, "updated_by": created_by},
                "lecture_id = %s AND day_of_week = %s", (lecture_id, day),
            )
    return lecture_id, created


def seed():
    """Seed demo accounts and master data without deleting existing records."""
    scheduler_username = os.getenv("SEED_SCHEDULER_USERNAME", "demo_scheduler")
    scheduler_email = os.getenv("SEED_SCHEDULER_EMAIL", "demo.scheduler@example.test")
    scheduler_password = _required_env("SEED_SCHEDULER_PASSWORD")
    professor_username = os.getenv("SEED_PROFESSOR_USERNAME", "demo_professor")
    professor_email = os.getenv("SEED_PROFESSOR_EMAIL", "demo.professor@example.test")
    professor_password = _required_env("SEED_PROFESSOR_PASSWORD")

    scheduler_id, scheduler_created = _ensure_user(
        scheduler_username, scheduler_email, scheduler_password, "scheduler"
    )
    professor_user_id, professor_created = _ensure_user(
        professor_username, professor_email, professor_password, "professor"
    )

    professor_id, professor_record_created = _ensure_professor(
        {
            "user_id": professor_user_id,
            "employee_code": "DEMO-P-001",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": professor_email,
        },
        scheduler_id,
    )
    course_id, course_created = _ensure_course(
        {
            "course_code": "DEMO-CS101",
            "course_name": "Introduction to Computing",
            "description": "Sample course for local timetable development.",
        },
        scheduler_id,
    )
    room_id, room_created = _ensure_room(
        {"room_code": "DEMO-ROOM-101", "room_name": "Demo Classroom 101"},
        scheduler_id,
    )
    verification_room_id, verification_room_created = _ensure_room(
        {"room_code": "DEMO-ROOM-102", "room_name": "Demo Classroom 102"},
        scheduler_id,
    )
    term_id, term_created = _ensure_term(
        {
            "term_name": "Demo Term 2026",
            "start_date": "2026-08-01",
            "end_date": "2026-12-15",
        },
        scheduler_id,
    )
    verification_term_id, verification_term_created = _ensure_term(
        {"term_name": "Demo Term 2027", "start_date": "2027-08-01", "end_date": "2027-12-15"},
        scheduler_id,
    )
    period = db.select_one(
        "SELECT id FROM dbo.periods WHERE period_number = %s AND is_active = 1", (1,)
    )
    if period is None:
        raise RuntimeError("Period 1 must be seeded before demo verification data.")
    lecture_id, lecture_created = _ensure_lecture(
        {"course_id": course_id, "professor_id": professor_id, "room_id": room_id, "term_id": term_id, "period_id": period["id"]},
        weekdays=[3], created_by=scheduler_id,
    )

    records = {
        "scheduler_user": scheduler_id,
        "professor_user": professor_user_id,
        "professor": professor_id,
        "course": course_id,
        "room": room_id,
        "verification_room": verification_room_id,
        "term": term_id,
        "verification_term": verification_term_id,
        "lecture": lecture_id,
    }
    created = {
        "scheduler_user": scheduler_created,
        "professor_user": professor_created,
        "professor": professor_record_created,
        "course": course_created,
        "room": room_created,
        "verification_room": verification_room_created,
        "term": term_created,
        "verification_term": verification_term_created,
        "lecture": lecture_created,
    }
    return records, created


if __name__ == "__main__":
    ids, created = seed()
    for name, record_id in ids.items():
        action = "created" if created[name] else "already existed"
        print(f"{name}: {action} (id={record_id})")
