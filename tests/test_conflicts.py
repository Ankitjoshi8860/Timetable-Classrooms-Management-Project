import unittest
from unittest.mock import patch

from services.conflicts import (
    find_professor_conflict,
    find_recurring_room_conflict,
    find_room_conflict,
)


class RoomConflictTests(unittest.TestCase):
    @patch("services.conflicts.db.select_one")
    def test_same_room_is_detected_for_matching_term_period_and_day(self, select_one):
        select_one.return_value = {"id": 10, "room_id": 1, "room_code": "A-101", "day_of_week": 1}

        conflict = find_room_conflict(term_id=1, room_id=1, period_id=2, weekdays=[1, 3])

        self.assertEqual(conflict["room_code"], "A-101")
        params = select_one.call_args.args[1]
        self.assertEqual(params, (1, 1, 2, 1, 3))

    @patch("services.conflicts.db.select_one", return_value=None)
    def test_different_room_is_available(self, select_one):
        self.assertIsNone(find_room_conflict(term_id=1, room_id=2, period_id=2, weekdays=[1]))

    @patch("services.conflicts.db.select_one")
    def test_edit_can_exclude_its_current_lecture(self, select_one):
        select_one.return_value = None

        self.assertIsNone(find_room_conflict(1, 1, 2, [1], exclude_lecture_id=10))
        self.assertEqual(select_one.call_args.args[1], (1, 1, 2, 1, 10))


class ProfessorConflictTests(unittest.TestCase):
    @patch("services.conflicts.db.select_one")
    def test_same_professor_is_detected_even_when_room_differs(self, select_one):
        select_one.return_value = {
            "id": 12,
            "professor_id": 1,
            "first_name": "Ada",
            "last_name": "Lovelace",
            "day_of_week": 1,
        }

        conflict = find_professor_conflict(term_id=1, professor_id=1, period_id=2, weekdays=[1])

        self.assertEqual(conflict["professor_id"], 1)
        params = select_one.call_args.args[1]
        self.assertEqual(params, (1, 1, 2, 1))

    @patch("services.conflicts.db.select_one", return_value=None)
    def test_different_professor_is_available(self, select_one):
        self.assertIsNone(find_professor_conflict(term_id=1, professor_id=2, period_id=2, weekdays=[1]))

    @patch("services.conflicts.db.select_one")
    def test_professor_edit_can_exclude_its_current_lecture(self, select_one):
        select_one.return_value = None

        self.assertIsNone(find_professor_conflict(1, 1, 2, [1], exclude_lecture_id=12))
        self.assertEqual(select_one.call_args.args[1], (1, 1, 2, 1, 12))


class RecurringInstanceConflictTests(unittest.TestCase):
    @patch("services.conflicts.db.select")
    @patch("services.conflicts.db.select_one")
    def test_later_recurrence_date_is_a_conflict(self, select_one, select):
        select_one.return_value = {
            "start_date": __import__("datetime").date(2026, 8, 3),
            "end_date": __import__("datetime").date(2026, 8, 31),
        }
        select.return_value = [{
            "id": 20,
            "resource_id": 1,
            "start_date": __import__("datetime").date(2026, 8, 3),
            "end_date": __import__("datetime").date(2026, 8, 31),
            "day_of_week": 3,
            "room_code": "A-101",
            "first_name": "Ada",
            "last_name": "Lovelace",
        }]

        conflict = find_recurring_room_conflict(1, 1, 2, [1, 3, 5])

        self.assertEqual(conflict["conflict_date"], __import__("datetime").date(2026, 8, 5))

    @patch("services.conflicts.db.select", return_value=[])
    @patch("services.conflicts.db.select_one")
    def test_excluded_lecture_is_not_a_recurring_conflict(self, select_one, select):
        select_one.return_value = {
            "start_date": __import__("datetime").date(2026, 8, 3),
            "end_date": __import__("datetime").date(2026, 8, 31),
        }

        self.assertIsNone(find_recurring_room_conflict(1, 1, 2, [1, 3], exclude_lecture_id=20))


if __name__ == "__main__":
    unittest.main()
