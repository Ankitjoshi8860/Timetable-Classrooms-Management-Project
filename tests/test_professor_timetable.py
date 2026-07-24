import unittest
from unittest.mock import patch

from app import create_app


class ProfessorTimetableTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def _login_as(self, user_id=9):
        with self.client.session_transaction() as session:
            session["user_id"] = user_id

    @patch("app.routes.professor_timetable.db.select")
    @patch("app.auth.db.select_one")
    def test_professor_sees_only_their_own_timetable(self, select_one, select):
        self._login_as()
        select_one.return_value = {"id": 9, "username": "ada", "role": "professor", "professor_id": 4}
        select.side_effect = [
            [{"id": 2, "term_name": "Odd Semester 2026", "start_date": "2026-08-01", "end_date": "2026-12-15"}],
            [{"id": 3, "period_number": 1, "period_label": "Period 1"}],
            [{"period_id": 3, "day_of_week": 1, "course_code": "CS101", "course_name": "Computing", "room_code": "A-101", "room_name": "Lab"}],
        ]

        response = self.client.get("/my-timetable")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CS101", response.data)
        self.assertIn(b"A-101", response.data)
        lecture_query_params = select.call_args_list[2].args[1]
        self.assertEqual(lecture_query_params, (2, 4))

    @patch("app.auth.db.select_one")
    def test_scheduler_cannot_open_professor_timetable(self, select_one):
        self._login_as()
        select_one.return_value = {"id": 9, "username": "scheduler", "role": "scheduler", "professor_id": None}

        response = self.client.get("/my-timetable")

        self.assertEqual(response.status_code, 403)

    @patch("app.auth.db.select_one")
    def test_professor_without_linked_record_is_forbidden(self, select_one):
        self._login_as()
        select_one.return_value = {"id": 9, "username": "orphan", "role": "professor", "professor_id": None}

        response = self.client.get("/my-timetable")

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
