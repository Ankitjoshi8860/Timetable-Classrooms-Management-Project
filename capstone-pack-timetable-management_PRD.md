# Capstone Pack — Timetable & Classroom Management (Flask)

Student capstone pool app. Trainees receive only the Opening Statement below — everything after it is the instructor's answer key, not shown to trainees up front.

---

## 1. Opening Statement

> A small college needs help scheduling classes. There are professors, courses, rooms, and lectures that need to happen somewhere at some time, and right now it's all done by hand on a whiteboard, which leads to mistakes. Build a system for scheduling staff to allocate lectures to rooms and time slots, and make sure nothing gets double-booked. Professors should be able to see their own schedule.

*(6 lines. Seeded ambiguity: it never says whether this timetable resets each semester/term or is one continuous ongoing schedule — trainees must ask. Hidden complexity: "make sure nothing gets double-booked" sounds like one rule but is actually two — a room can't host two lectures at once, AND a professor can't teach two lectures at once, even in different rooms — and it must hold for recurring weekly lectures, not just one-off ones.)*

---

## 2. Instructor Answer Key

### Expected Entities
- **User** — scheduling staff / admin account (and optionally a professor login).
- **Professor** — name, department, contact info.
- **Course** — name/code, department, credit hours.
- **Room** — name/number, building, capacity.
- **Term/Semester** — if scoping is resolved toward term-based (start/end dates, name).
- **Lecture** — the schedulable unit: course + professor + room + day(s) + time slot (+ term, if scoped). Recurring lectures (e.g. "Mon/Wed/Fri 10–11") should be modeled as one recurring entry that expands into checkable instances, not one row per calendar date.

### Expected Roles
**Scheduler/Admin** — creates/edits professors, courses, rooms, and allocates lectures. **Professor** (optional, lighter role) — read-only view of their own schedule. A team that decides this is admin-only and documents that choice is acceptable; a team that silently builds no auth at all is not.

### Expected Screens
1. Login.
2. Admin dashboard.
3. Professors CRUD.
4. Courses CRUD.
5. Rooms CRUD.
6. Allocation screen — form to schedule a lecture (course, professor, room, day/time, term) with conflict feedback before save.
7. Timetable grid view — by room or by professor, showing the week's schedule.
8. Professor's own schedule view (if that role is in scope).

### Expected Clarifying Questions (Resolved Specifications)

**1. Is the timetable scoped per term/semester or continuous?**
* **Resolved (Term-Based):** The scheduling system is scoped by academic term/semester (e.g., Odd Semester 2026). This allows administrative staff to plan future semesters while the current semester is active without data overlap.

**2. What's the time-slot granularity?**
* **Resolved (Fixed Periods):** The system uses a standardized grid of fixed periods (e.g., Period 1, Period 2) rather than arbitrary start and end times. This ensures uniform scheduling across the college and provides robust, predictable conflict validation.

**3. When a scheduling conflict is detected, how is it handled?**
* **Resolved (Hard Block):** The system enforces strict data integrity. If a scheduling conflict is detected (either a room double-booking or a professor double-booking), the system issues a hard block, rejecting the save and requiring the scheduler to select a valid time slot.

**4. Are lectures one-off sessions or recurring?**
* **Resolved (Recurring Pattern):** Lectures are scheduled on a weekly recurring pattern for the duration of the term (e.g., Every Monday and Wednesday for Period 1). The conflict validation engine will check every generated instance of the recurring pattern to ensure no overlaps exist on any specific calendar date.

**5. Do rooms have capacity limits checked against class size?**
* **Resolved (Out of Scope):** Tracking room capacity versus expected student enrollment is out of scope for this phase. The allocation engine strictly validates time and location availability to prevent double-booking.

**6. Is there a professor-facing view?**
* **Resolved (Multi-Role Access):** The system features dual roles. The Scheduler/Admin role has full CRUD and allocation permissions. The Professor role is restricted to a read-only view of their personal timetable.


### Suggested Phase Split → GitHub Milestones

**Milestone 1 — Scaffold, Schema, Auth**
1. Flask app scaffold (blueprints, config, DB connection)
2. Schema: users, professors, courses, rooms, terms (if scoped), lectures
3. Auth: login/logout, password hashing, role check (scheduler vs professor, if in scope)
4. Seed script: a handful of professors, courses, rooms

**Milestone 2 — Core CRUD**
1. Professor CRUD
2. Course CRUD
3. Room CRUD
4. Term CRUD (if term-scoping was chosen)
5. Basic list/detail pages for each

**Milestone 3 — Allocation Engine + Conflict Prevention**
1. Lecture scheduling form (course, professor, room, day/time, term)
2. Room double-booking check — reject/flag overlapping time on same room/day
3. Professor double-booking check — reject/flag overlapping time for same professor across any room
4. Recurring lecture support (weekly pattern) with conflict checks applied across all generated instances, not just the first
5. Timetable grid view (filter by room or professor)

**Milestone 4 — Polish**
1. Professor's own read-only schedule view (if in scope)
2. Edit/reschedule an existing lecture, re-validating conflicts excluding itself
3. Seed data deliberately including near-overlaps (to prove conflict checks work, not just look plausible)
4. Production sanity check (no debug mode, no hardcoded secrets)

---

## 3. Acceptance Criteria

- Scheduling two lectures in the same room with overlapping time on the same day is rejected (or clearly flagged, per the team's chosen policy) with a specific error identifying the conflict.
- Scheduling the same professor for two overlapping time slots — even in different rooms — is rejected the same way.
- A recurring lecture (e.g. Mon/Wed/Fri 10–11) is checked for conflicts across every day it recurs on, not just validated once against the first occurrence.
- Editing or moving an existing lecture re-runs the conflict check excluding the lecture's own current slot (so saving it unchanged doesn't falsely flag itself as a conflict).
- The timetable grid view, filtered by a given room or professor, accurately shows every lecture scheduled against it for the current term/week.
- If term-scoping was chosen: the same room and professor are correctly treated as free in a different term even if they're busy in the current one.
- Only the scheduler/admin role (per the team's resolved role model) can create or edit allocations.

---

## 4. Rubric Mapping

**Spec quality (25):** Full marks requires the fine-tuned PRD to explicitly state the term-scoping decision and the time-slot granularity, and to spell out both halves of "no double-booking" (room-level and professor-level) as separate, named requirements rather than one vague line. A spec that only mentions room conflicts and misses the professor-conflict half is incomplete regardless of code quality.

**Git/milestone discipline (25):** Milestones matching the phase split above, with the conflict-checking logic tracked as its own issue(s) in Milestone 3 — separate from "build the allocation form" — since this is the part of the spec most likely to be rushed. Commits should show the conflict logic evolving distinctly from the basic CRUD.

**Working app (30):** The core value of this app is the conflict prevention — full marks requires demonstrating, live, that a double-booking attempt (room and professor, including at least one recurring-lecture case) is actually rejected, not merely that CRUD screens exist. All core CRUD (professors, courses, rooms, lectures) must be functional end-to-end.

**Diff-review evidence & corrections (20):** Full marks looks for a documented catch of an agent mistake specific to this app's trap — commonly, the agent implementing the conflict check against the literal new lecture's single date but forgetting to expand a recurring pattern across all its future occurrences, or checking room conflicts but forgetting the professor-conflict check entirely. Evidence should show the trainee spotted this in the diff (not in later manual testing) and the corrected commit.


## 5. Spec List

**1. Users & roles**
* **Admin/Scheduler:** Full access to manage the system. Can create, read, update, and soft-delete master data (Professors, Courses, Rooms, Terms) and allocate lectures.
* **Professor:** Restricted access. Can only log in to view a read-only grid of their own scheduled lectures.

**2. Entities**
* **User:** Login credentials and role definitions.
* **Professor:** Name, department, contact info.
* **Course:** Name/code, department, credit hours.
* **Room:** Name/number, building.
* **Term:** Academic semester boundaries (e.g., Odd Semester 2026).
* **Lecture:** The schedulable unit linking Course + Professor + Room + Term + Time Slot.
* *(Note: All entities include mandatory audit columns: id, is_active, created_by, updated_by, created_at, updated_at).*

**3. Screens**
* Login Page.
* Admin Dashboard (Metrics/Activity summary).
* Master Data List Screens (Professors, Courses, Rooms, Terms) utilizing jQuery DataTables and single-modal Add/Edit forms.
* Lecture Allocation Form.
* Timetable Grid View (Filterable by Room or Professor).
* Professor's Personal Read-Only Schedule View.

**4. Key flow**
* **The Allocation & Conflict Engine:** The admin selects a Course, Professor, Room, Term, and a weekly recurring Time Slot (e.g., Period 1 on Mondays). The system calculates all recurring instances of that lecture. It then runs a strict validation to ensure the Room is not double-booked AND the Professor is not double-booked. If a conflict is found, the system issues a hard block and rejects the save. 

**5. Out of scope**
* Tracking room capacity limits against expected student enrollment sizes.
* Arbitrary, minute-by-minute start and end times (the system strictly uses standardized fixed periods).

**6. Non-functional**
* **Stack:** Python/Flask backend, strictly routing all SQL Server operations through the provided `services/db.py` wrapper. 
* **Security:** Password hashing and strict server-side permission checks for all CRUD routes based on user role.
* **Data Integrity:** Soft deletes only (via `is_active` flag) and comprehensive activity logging for all status/ownership changes.
* **UI/UX Standard:** Strict adherence to the 60:30:10 colour palette (#F4F7F6, #FFFFFF, #0D6EFD) and Bootstrap Icons.