# Timetable Classroom Management

Flask application for managing academic terms, classrooms, professors, courses,
and recurring lecture allocations.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set local values.
4. Start the app with `flask --app run:app run --debug`.

The application factory can also be imported directly:

```python
from app import create_app

app = create_app()
```

Use `APP_CONFIG=production` when running outside development. All database
access goes through `services/db.py`.

## Local demo seed

Copy the seed credential variables from `.env.example` into your local `.env`
and replace the placeholder passwords with local-only values. Then run
`python -m database.seed` from the project root. The script creates demo users,
professors, a course, verification classrooms, verification terms, and one valid
recurring lecture through `services/db.py`; it does not delete or overwrite
existing records or insert invalid conflicting allocations. The demo passwords
are intentionally not stored in the repository.

## Conflict verification scenarios

After seeding, run `python -m database.verify_conflicts`. This read-only command
reports proof for room conflicts, professor conflicts in different rooms, later
recurring-instance conflicts, and reuse in another term.
