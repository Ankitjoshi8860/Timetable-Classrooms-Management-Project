import unittest
from unittest.mock import patch

from services.conflicts import find_room_conflict


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


if __name__ == "__main__":
    unittest.main()
