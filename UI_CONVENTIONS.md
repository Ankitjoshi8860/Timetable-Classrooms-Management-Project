# Timetable Classroom management App - UI & Engineering Conventions

* **Stack:** Python/Flask. Do not invent custom layout conventions; follow the rules below strictly.
* **Overall shell:** persistent, collapsible sidebar navigation + header, with each module's page rendering inside a card container. Sidebar should reflect the logged-in user's role/permissions and collapse to icon-only on smaller screens/toggle.
* **List screens:** every object (students, assets, deals, lectures, awards, etc.) gets a list screen inside a card — card header has the icon + page title on the left, 1–3 compact filters and a "New [Object]" button on the right. Filters reload the table in place; they should not navigate to a new page. Use jQuery DataTables for every list screen (sortable, paginated, responsive) rather than a plain HTML table — switch to server-side paging only if a table can grow large.
* **Icons:** Bootstrap Icons only — no mixing icon sets.
* **Color scheme (60:30:10 rule):** All UI elements must strictly use this palette:
  * Dominant/Background (60%): `#F4F7F6` (Light grayish-blue)
  * Secondary/Surface (30%): `#FFFFFF` (White)
  * Accent/Primary Actions (10%): `#0D6EFD` (Bootstrap Blue)
* **Add/Edit:** one modal handles both create and edit for a given object — Edit just opens the same modal pre-populated. Don't build separate create pages unless the form genuinely needs multiple sections, file uploads, or child records.
* **Delete:** always behind a confirmation step. Use soft-delete (an is_active/deleted_at-style flag) instead of a hard delete wherever the record has audit or relationship importance (payments, stage history, attendance, etc.).
* **Row actions:** edit/delete/view as icon-only buttons in the rightmost column, each with an accessible label.
* **Common fields:** every table should carry id, is_active, created_by, updated_by, created_at, updated_at at minimum.
* **API/route pattern:** one route file/blueprint per module, with consistent actions across all apps — list, get, save, delete (add toggle_active/assign/export only if the workflow needs it). No business logic in templates, no page-building logic inside API routes.
* **Auth & permissions:** every module should be readable per-role, with view/create/edit/delete permissions checked both in the route and reflected in the UI (hide buttons the user can't use — but never rely on hiding alone, enforce it server-side too).
* **Activity logging:** log role changes, status changes, deletes/restores, and ownership changes — capture entity type, entity id, action, old/new value, user, timestamp.
* **Accessibility basics:** aria-label on icon-only buttons, visible focus states, Escape closes modals, modals have titles.
* **Database Operations:** All database operations must go through the provided DB wrapper — do not call the DB driver directly from inside modules.