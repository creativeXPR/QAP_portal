# QAP Developer Guide

## Architecture

The Quality Assurance Platform is split into two applications:

- `QAP_portal`: Django 5.2 and Django REST Framework backend.
- `QAP_frontend`: React 19, Vite, Tailwind CSS frontend.

The frontend talks to the backend through `src/api/client.js` and `src/api/services.js`. Authentication uses JWT access tokens stored in browser local storage and sent as `Authorization: Bearer <token>`.

## Backend Folder Structure

- `qap_backend/`: Django project settings, URL routing, WSGI and ASGI entry points.
- `authentication/`: username/email login, registration, Google login, profile completion, role profile.
- `core/`: faculties and departments.
- `courses/`: courses and lecture session monitoring.
- `lecturers/`: lecturer profiles and assessment reports.
- `examinations/`: exam sessions and exam quality reports.
- `students/`: student records, feedback, complaints, attachments, notifications.
- `accreditation/`: accreditation cycles, metrics, submissions, evidence, alerts, corrective actions, PARI calculations.
- `analytics/`: analytics formula services and accreditation analytics endpoints.
- `dashboards/`: aggregated dashboards and activity feeds.
- `qa_committee/`: committees, meetings, audit cycles, findings, recommendations, action plans, evidence, reports, data reviews.
- `documents/`: institutional document repository, versions, access logs, publication workflow.
- `docs/`: system documentation.

## Frontend Folder Structure

- `src/App.jsx`: route definitions and role-protected pages.
- `src/api/client.js`: fetch wrapper, auth headers, errors, resource helper.
- `src/api/services.js`: frontend endpoint map.
- `src/lib/`: auth helpers, submission mapping, date and university/classification helpers.
- `src/components/common/`: shared route guards and async state components.
- `src/components/dashboard/`: reusable dashboard cards, tables, charts.
- `src/components/student/`: student layout, sidebar, top bar, report wizard.
- `src/pages/`: role dashboards, auth screens, profile screens, student screens.

## Installation

Backend:

```powershell
cd QAP_portal
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

Frontend:

```powershell
cd QAP_frontend
npm install
```

## Environment Variables

Backend:

- `DJANGO_SECRET_KEY`: required in production.
- `DJANGO_DEBUG`: `true` or `false`; set `false` in production.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hosts.
- `DATABASE_URL`: optional database URL; falls back to SQLite.
- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins.
- `CSRF_TRUSTED_ORIGINS`: comma-separated trusted HTTPS origins.
- `GOOGLE_CLIENT_ID`: Google OAuth client ID.

Frontend:

- `VITE_API_BASE_URL`: backend origin, for example `http://127.0.0.1:8000`.

## Running Locally

Backend:

```powershell
cd QAP_portal
python manage.py runserver 127.0.0.1:8000
```

Frontend:

```powershell
cd QAP_frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## Database Setup

The backend uses SQLite by default. When `DATABASE_URL` is present, `dj_database_url` configures the production database. Run migrations after changing models:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Seed dashboard demo data:

```powershell
python manage.py seed_dashboard_demo_data
```

Seed departments:

```powershell
python manage.py seed_departments
```

## Authentication Flow

1. User registers through `POST /api/auth/google/register/` or logs in through `POST /api/auth/login/`.
2. Backend returns `access`, `refresh`, `user`, `user_id`, and `profile_complete`.
3. Frontend stores `access_token`, `refresh_token`, `auth_type`, `user`, `user_id`, and `user_role`.
4. `ProtectedRoute` checks authentication and allowed roles.
5. API calls attach `Authorization: Bearer <access_token>`.

Supported profile statuses:

- `student`
- `focal_person`
- `principle_officer`
- `admin`

Additional backend dashboard and QA roles exist for permission checks: `dqa_admin`, `super_admin`, `qa_focal_person`, `committee_chairperson`, `committee_secretary`, `committee_member`, `department_admin`, `faculty_admin`, `read_only_viewer`.

## Module Relationships

- Faculties own departments.
- Departments own courses.
- Students belong to faculties and departments and can be linked to courses.
- Courses are referenced by lecture sessions and examination sessions.
- Lecturer profiles are assessed through assessment reports.
- Accreditation cycles contain components, metrics, submissions, evidence, alerts, corrective actions, component scores, and PARI results.
- Dashboards aggregate data from accreditation, QA committee, teaching, examinations, documents, student feedback, infrastructure, and research modules.
- QA committees run meetings, audits, findings, recommendations, action plans, evidence, reports, and data reviews.
- Documents can be submitted, reviewed, approved, rejected, published, archived, versioned, previewed, and downloaded.
- Student feedback updates create student notifications.

## Deployment

Backend production checklist:

- Set `DJANGO_DEBUG=false`.
- Set a unique `DJANGO_SECRET_KEY`.
- Set `DJANGO_ALLOWED_HOSTS`.
- Set `DATABASE_URL` for PostgreSQL or another production database.
- Set `CORS_ALLOWED_ORIGINS` to the deployed frontend origin only.
- Set `CSRF_TRUSTED_ORIGINS` for HTTPS origins.
- Run `python manage.py migrate`.
- Run `python manage.py collectstatic` if static assets are served by Django.

Frontend production checklist:

- Set `VITE_API_BASE_URL` to the deployed backend origin.
- Run `npm run build`.
- Deploy `dist/` to the frontend host.

## Testing

Backend:

```powershell
python manage.py check
python manage.py test
```

Frontend:

```powershell
npm run lint
npm run build
```

Useful targeted backend suites:

```powershell
python manage.py test authentication core courses examinations lecturers
python manage.py test accreditation analytics
python manage.py test students documents
python manage.py test dashboards qa_committee
```

## Troubleshooting

- 401 responses: confirm access token exists and `Authorization` header is `Bearer <token>`.
- 403 responses: confirm the user's profile status is allowed for the endpoint.
- CORS failure: set `CORS_ALLOWED_ORIGINS` to the exact frontend origin.
- CSRF failure on cookie/session endpoints: add the HTTPS frontend origin to `CSRF_TRUSTED_ORIGINS`.
- Empty dashboard: seed demo data or create source records in accreditation, QA committee, documents, examinations, and student feedback.
- File upload rejected: student feedback accepts `.jpg`, `.jpeg`, `.png`, `.pdf` up to 1 MB.
- Frontend API target wrong: set `VITE_API_BASE_URL`.
