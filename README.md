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

Use `APP_CONFIG=production` when running outside development. Database access
will be added through `services/db.py` as later milestones implement the schema
and feature modules.
