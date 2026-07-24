import unittest
from unittest.mock import MagicMock, patch

from app import create_app


class AllocationEditTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def _login_as(self, user_id=9):
        with self.client.session_transaction() as session:
            session["user_id"] = user_id

    @patch("app.routes.allocations.log_event")
    @patch("app.routes.allocations.db.begin_transaction")
    @patch("app.routes.allocations.find_recurring_professor_conflict", return_value=None)
    @patch("app.routes.allocations.find_recurring_room_conflict", return_value=None)
    @patch("app.routes.allocations.db.select", return_value=[{"day_of_week": 1}, {"day_of_week": 3}])
    @patch("app.routes.allocations.db.select_one")
    def test_unchanged_edit_excludes_current_lecture_from_conflicts(
        self,
        select_one,
        select,
        room_conflict,
        professor_conflict,
        transaction,
        log_event,
    ):
        self._login_as()
        select_one.side_effect = [
            {"id": 9, "username": "scheduler", "role": "scheduler", "professor_id": None},
            {"id": 8, "course_id": 1, "professor_id": 2, "room_id": 3, "term_id": 4, "period_id": 5},
            {"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5},
        ]
        cursor = MagicMock()
        transaction.return_value.__enter__.return_value = cursor

        response = self.client.post(
            "/allocations/8/edit",
            data={
                "course_id": "1", "professor_id": "2", "room_id": "3",
                "term_id": "4", "period_id": "5", "days": ["1", "3"],
            },
        )

        self.assertEqual(response.status_code, 302)
        room_conflict.assert_called_once_with(4, 3, 5, [1, 3], exclude_lecture_id=8)
        professor_conflict.assert_called_once_with(4, 2, 5, [1, 3], exclude_lecture_id=8)
        self.assertEqual(cursor.execute.call_count, 4)
        log_event.assert_called_once()
        self.assertEqual(log_event.call_args.kwargs["action"], "update")
        self.assertEqual(log_event.call_args.kwargs["entity_id"], 8)

    @patch("app.routes.allocations.db.begin_transaction")
    @patch("app.routes.allocations.find_recurring_room_conflict")
    @patch("app.routes.allocations.db.select", return_value=[{"day_of_week": 1}])
    @patch("app.routes.allocations.db.select_one")
    def test_conflicting_edit_is_hard_blocked_before_update(
        self, select_one, select, room_conflict, transaction
    ):
        self._login_as()
        select_one.side_effect = [
            {"id": 9, "username": "scheduler", "role": "scheduler", "professor_id": None},
            {"id": 8, "course_id": 1, "professor_id": 2, "room_id": 3, "term_id": 4, "period_id": 5},
            {"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5},
        ]
        room_conflict.return_value = {"room_code": "A-101"}

        response = self.client.post(
            "/allocations/8/edit",
            data={
                "course_id": "1", "professor_id": "2", "room_id": "3",
                "term_id": "4", "period_id": "5", "days": ["1"],
            },
        )

        self.assertEqual(response.status_code, 302)
        transaction.assert_not_called()

    @patch("app.auth.db.select_one")
    def test_professor_cannot_edit_an_allocation(self, select_one):
        self._login_as()
        select_one.return_value = {
            "id": 9, "username": "professor", "role": "professor", "professor_id": 2,
        }

        response = self.client.get("/allocations/8/edit")

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
