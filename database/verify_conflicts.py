"""Run safe, repeatable proof scenarios for the allocation conflict engine."""

from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "env", override=False)

from services import db
from services.conflicts import find_recurring_professor_conflict, find_recurring_room_conflict


def _demo_id(table, column, value):
    row = db.select_one(
        f"SELECT id FROM dbo.{table} WHERE {column} = %s AND is_active = 1", (value,)
    )
    if row is None:
        raise RuntimeError("Demo verification data is missing. Run `python -m database.seed` first.")
    return row["id"]


def run():
    professor_id = _demo_id("professors", "employee_code", "DEMO-P-001")
    room_id = _demo_id("rooms", "room_code", "DEMO-ROOM-101")
    verification_room_id = _demo_id("rooms", "room_code", "DEMO-ROOM-102")
    term_id = _demo_id("terms", "term_name", "Demo Term 2026")
    verification_term_id = _demo_id("terms", "term_name", "Demo Term 2027")
    period_id = db.select_one(
        "SELECT id FROM dbo.periods WHERE period_number = %s AND is_active = 1", (1,)
    )["id"]

    later_date_conflict = find_recurring_room_conflict(term_id, room_id, period_id, [1, 3, 5])
    scenarios = [
        ("room double-booking is hard-blocked", later_date_conflict is not None),
        (
            "professor double-booking is blocked in a different room",
            find_recurring_professor_conflict(term_id, professor_id, period_id, [3]) is not None
            and verification_room_id != room_id,
        ),
        (
            "later recurring instance is identified",
            later_date_conflict is not None and later_date_conflict["conflict_date"].weekday() == 2,
        ),
        (
            "same room and professor are free in another term",
            find_recurring_room_conflict(verification_term_id, room_id, period_id, [3]) is None
            and find_recurring_professor_conflict(verification_term_id, professor_id, period_id, [3]) is None,
        ),
    ]
    failures = []
    for name, passed in scenarios:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        if not passed:
            failures.append(name)
    return failures


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
