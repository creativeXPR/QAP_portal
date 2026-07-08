# QAP API Reference

Base URL: `http://127.0.0.1:8000`

Authenticated endpoints require:

```http
Authorization: Bearer <access_token>
```

Common DRF errors:

- `400`: validation error.
- `401`: missing or invalid authentication.
- `403`: authenticated but not permitted.
- `404`: record not found or hidden by visibility/ownership rules.

Some modules return plain serializer data. Accreditation and institutional documents return envelopes:

```json
{
  "success": true,
  "message": "Request completed successfully.",
  "data": {},
  "pagination": {
    "count": 0,
    "next": null,
    "previous": null
  }
}
```

## Authentication

### `POST /api/auth/login/`

Body:

```json
{
  "username": "dqa_admin",
  "password": "StrongPass123!"
}
```

Response:

```json
{
  "refresh": "<jwt>",
  "access": "<jwt>",
  "profile_complete": true,
  "user_id": 1,
  "user": {
    "id": 1,
    "username": "dqa admin",
    "email": "dqa_admin@example.com",
    "status": "admin",
    "full_name": "dqa admin",
    "first_name": "",
    "last_name": ""
  }
}
```

### `POST /api/auth/google/register/`

Body:

```json
{
  "username": "student_user",
  "email": "student@example.com",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!",
  "status": "student"
}
```

Valid `status`: `student`, `focal_person`, `principle_officer`, `admin`.

### `POST /api/auth/google/`

Body:

```json
{
  "id_token": "<google-id-token>"
}
```

### `POST /api/auth/google/complete-profile/`

Auth required. Body:

```json
{
  "username": "student_user",
  "status": "student"
}
```

### dj-rest-auth endpoints

- `POST /api/auth/password/reset/`
- `POST /api/auth/password/reset/confirm/`
- `POST /api/auth/logout/`
- `GET|PUT|PATCH /api/auth/user/`
- `POST /api/auth/password/change/`
- `POST /api/auth/registration/`
- `POST /api/auth/registration/verify-email/`
- `POST /api/auth/registration/resend-email/`

## CRUD Endpoint Convention

Unless noted otherwise, these resources support:

- `GET /resource/`: list.
- `POST /resource/`: create.
- `GET /resource/{id}/`: retrieve.
- `PUT /resource/{id}/`: replace.
- `PATCH /resource/{id}/`: partial update.
- `DELETE /resource/{id}/`: delete.

List endpoints commonly support module-specific filters plus `search` where implemented. Paginated modules accept `page` and `page_size`.

## Core

### Faculties: `/api/core/faculties/`

Fields: `id`, `name`.

Example create:

```json
{
  "name": "Faculty of Science"
}
```

### Departments: `/api/core/departments/`

Fields: `id`, `faculty`, `faculty_name`, `name`.

Example create:

```json
{
  "faculty": 1,
  "name": "Computer Science"
}
```

Filters: `search`.

## Courses

### Courses: `/api/courses/courses/`

Fields include department reference, course code, and course title.

Example:

```json
{
  "department": 1,
  "code": "CSC 101",
  "title": "Introduction to Computing"
}
```

### Lecture Sessions: `/api/courses/lecture-sessions/`

Creates lecture monitoring records linked to courses and respondents. Tested fields include `course`, `respondent`, `monitored_at`, `time_slot`, `level`, `mode`, `lecturer_present`, `actual_duration`, `venue`, `held`, `estimated_attendance`, `classroom_environment_rating`, `teaching_effectiveness_rating`.

## Lecturers

### Lecturer Profiles: `/api/lecturers/lecturer-profiles/`

CRUD for lecturer identity/profile records.

### Lecturer Assessment Summary

`GET /api/lecturers/lecturer-profiles/{id}/assessment_summary/`

Returns aggregated assessment summary for the lecturer.

### Assessment Reports: `/api/lecturers/assessment-reports/`

CRUD for lecturer assessment report records.

## Examinations

### Exam Sessions: `/api/examinations/exam-sessions/`

Example:

```json
{
  "department": 1,
  "course_code_title": "CSC 101",
  "exam_date": "2026-07-08",
  "venue": "Hall A",
  "academic_session": "2025/2026"
}
```

### Quality Reports: `/api/examinations/quality-reports/`

Creates exam quality ratings for seating, lighting, ventilation, instructions, invigilation, organization, misconduct, and overall rating.

## Students

### Students: `/api/students/`

Fields: `id`, `user`, `matric_number`, `first_name`, `last_name`, `full_name`, `email`, `faculty`, `faculty_name`, `department`, `department_name`, `programme`, `level`, `status`, `courses`, `course_codes`, `created_at`, `updated_at`.

Example:

```json
{
  "user": 2,
  "matric_number": "CSC/2026/001",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@student.example.com",
  "faculty": 1,
  "department": 1,
  "programme": "BSc Computer Science",
  "level": "100",
  "status": "active",
  "courses": [1]
}
```

Validation:

- Department must belong to selected faculty.
- Courses must belong to selected department.
- Matric number is normalized to uppercase.

### Feedback and Complaints

Endpoints:

- `GET|POST /api/students/feedback-tracking/`
- `GET|POST /api/students/feedback/`
- `GET|PUT|PATCH|DELETE /api/students/feedback/{id}/`

Create body:

```json
{
  "student": "student_user",
  "student_email": "student@example.com",
  "feedback": "Lecture room needs better ventilation.",
  "category": "complaint",
  "classification": "academic",
  "urgency": "high",
  "submission_mode": "open_identity"
}
```

Valid categories: `complaint`, `suggestion`, `inquiry`, `support`, `other`.

Valid classifications include `academic`, `welfare`, `facility`, `administrative`, `other`.

Valid urgency values: `normal`, `high`, `critical`.

Multipart upload accepts `attachments`, `attachments[]`, or `attachment_uploads`. Allowed extensions: `.jpg`, `.jpeg`, `.png`, `.pdf`; max size: 1 MB.

Manager-only update fields: `status`, `admin_comment`, `assigned_to`. Manager roles: `admin`, `principle_officer`, `focal_person`.

### Notifications

- `GET /api/students/notifications/`
- `GET /api/students/notifications/{id}/`
- `POST /api/students/notifications/{id}/mark-read/`

Response fields: `id`, `title`, `message`, `notification_type`, `user`, `complaint`, `complaint_id`, `is_read`, `created_at`.

## Accreditation

All endpoints require accreditation permissions and return the envelope shape.

CRUD endpoints:

- `/api/accreditation/cycles/`
- `/api/accreditation/components/`
- `/api/accreditation/metrics/`
- `/api/accreditation/submissions/`
- `/api/accreditation/evidence/`
- `/api/accreditation/alerts/`
- `/api/accreditation/actions/`

Common filters: `cycle`, `programme`, `faculty`, `department`, `status`, `component`, `reporting_period`, `risk_classification`, `date_from`, `date_to`.

Custom endpoints:

- `PATCH /api/accreditation/cycles/{id}/close/`
- `POST /api/accreditation/submissions/bulk/`
- `PATCH /api/accreditation/evidence/{id}/verify/`
- `PATCH /api/accreditation/evidence/{id}/reject/`
- `POST /api/accreditation/cycles/{cycle_id}/programmes/{programme_id}/calculate-component-scores/`
- `POST /api/accreditation/cycles/{cycle_id}/programmes/{programme_id}/calculate-pari/`
- `PATCH /api/accreditation/alerts/{id}/acknowledge/`
- `PATCH /api/accreditation/alerts/{id}/resolve/`
- `PATCH /api/accreditation/alerts/{id}/escalate/`
- `PATCH /api/accreditation/actions/{id}/progress/`
- `PATCH /api/accreditation/actions/{id}/submit/`
- `PATCH /api/accreditation/actions/{id}/verify/`
- `PATCH /api/accreditation/actions/{id}/reject/`
- `PATCH /api/accreditation/actions/{id}/close/`

Bulk submission example:

```json
{
  "cycle": 1,
  "programme": "BSc Computer Science",
  "reporting_period": "2025/2026",
  "submissions": [
    {
      "metric": 1,
      "value": "12",
      "comment": "Updated staffing count"
    }
  ]
}
```

Reviewer action example:

```json
{
  "reviewer_comment": "Accepted."
}
```

Progress example:

```json
{
  "progress_percentage": 60,
  "reviewer_comment": "Implementation ongoing."
}
```

## Analytics

All analytics endpoints are authenticated:

- `GET /api/analytics/accreditation/overview/`
- `GET /api/analytics/accreditation/programmes-by-risk/`
- `GET /api/analytics/accreditation/component-performance/`
- `GET /api/analytics/accreditation/early-warning/`
- `GET /api/analytics/accreditation/faculty-summary/`
- `GET /api/analytics/accreditation/department-summary/`
- `GET /api/analytics/accreditation/timeline/`

Responses are analytics-ready objects derived from accreditation cycles, component scores, PARI results, alerts, and related data.

## Dashboards

Dashboard endpoints require dashboard roles.

- `GET /api/dashboards/summary/`
- `GET /api/dashboards/university-overview/`
- `GET /api/dashboards/accreditation/`
- `GET /api/dashboards/qa-committee/`
- `GET /api/dashboards/teaching-learning/`
- `GET /api/dashboards/examinations/`
- `GET /api/dashboards/documents/`
- `GET /api/dashboards/student-experience/`
- `GET /api/dashboards/infrastructure-labs/`
- `GET /api/dashboards/research/`
- `GET /api/dashboards/early-warning/`
- `GET /api/dashboards/activity-feed/`

Filters:

- `faculty_id`
- `department_id`
- `period`
- `limit` for activity feed.

Dashboard response shape:

```json
{
  "success": true,
  "data": {
    "kpi_cards": [],
    "charts": {},
    "alerts": [],
    "recent_activity": []
  }
}
```

Department and faculty admin users must pass their own `department_id` or `faculty_id`.

## QA Committee

CRUD endpoints:

- `/api/qa-committee/committees/`
- `/api/qa-committee/members/`
- `/api/qa-committee/meetings/`
- `/api/qa-committee/attendance/`
- `/api/qa-committee/audit-cycles/`
- `/api/qa-committee/findings/`
- `/api/qa-committee/recommendations/`
- `/api/qa-committee/action-plans/`
- `/api/qa-committee/evidence/`
- `/api/qa-committee/reports/`
- `/api/qa-committee/data-reviews/`

Summary endpoints:

- `GET /api/qa-committee/summary/`
- `GET /api/qa-committee/effectiveness/`
- `GET /api/qa-committee/overdue-actions/`
- `GET /api/qa-committee/risk-summary/`
- `GET /api/qa-committee/activity-feed/`

Custom workflow endpoints:

- `GET|POST /api/qa-committee/committees/{id}/members/`
- `GET /api/qa-committee/committees/{id}/dashboard/`
- `POST /api/qa-committee/meetings/{id}/mark-held/`
- `POST /api/qa-committee/meetings/{id}/attendance/`
- `POST /api/qa-committee/audit-cycles/{id}/submit/`
- `POST /api/qa-committee/audit-cycles/{id}/close/`
- `POST /api/qa-committee/findings/{id}/resolve/`
- `POST /api/qa-committee/findings/{id}/dismiss/`
- `POST /api/qa-committee/recommendations/{id}/accept/`
- `POST /api/qa-committee/recommendations/{id}/mark-in-progress/`
- `POST /api/qa-committee/recommendations/{id}/mark-implemented/`
- `POST /api/qa-committee/recommendations/{id}/verify/`
- `POST /api/qa-committee/action-plans/{id}/submit-evidence/`
- `POST /api/qa-committee/evidence/{id}/verify/`
- `POST /api/qa-committee/evidence/{id}/reject/`
- `POST /api/qa-committee/reports/{id}/submit/`
- `POST /api/qa-committee/reports/{id}/approve/`
- `POST /api/qa-committee/data-reviews/{id}/validate/`
- `POST /api/qa-committee/data-reviews/{id}/flag/`

Meeting attendance example:

```json
{
  "attendance": [
    {
      "member": 1,
      "attendance_status": "present",
      "remarks": "Present"
    }
  ]
}
```

Evidence example:

```json
{
  "title": "Implementation evidence",
  "external_url": "https://example.com/evidence"
}
```

## Institutional Documents

Envelope response and pagination are used.

CRUD/read endpoints:

- `/api/institutional-documents/categories/`
- `/api/institutional-documents/documents/`
- `/api/institutional-documents/versions/`
- `/api/institutional-documents/access-logs/`

Document filters:

- `search`
- `category`
- `document_type`
- `related_module`
- `visibility_level`
- `status`
- `is_latest`
- `uploaded_by`
- `approved_by`
- `effective_date_from`
- `effective_date_to`
- `review_date_from`
- `review_date_to`
- `created_at_from`
- `created_at_to`

Document create example:

```json
{
  "title": "Quality Assurance Policy",
  "category": 1,
  "document_type": "pdf",
  "related_module": "institutional_policy",
  "visibility_level": "all_authenticated",
  "description": "Official QA policy.",
  "effective_date": "2026-07-08",
  "review_date": "2027-07-08",
  "change_summary": "Initial upload"
}
```

For `document_type: "pdf"`, send multipart `file`. For `document_type: "link"`, send `external_url`.

Workflow endpoints:

- `POST /api/institutional-documents/documents/{id}/submit-for-review/`
- `POST /api/institutional-documents/documents/{id}/approve/`
- `POST /api/institutional-documents/documents/{id}/reject/`
- `POST /api/institutional-documents/documents/{id}/publish/`
- `POST /api/institutional-documents/documents/{id}/archive/`
- `POST /api/institutional-documents/documents/{id}/new-version/`
- `GET /api/institutional-documents/documents/{id}/preview/`
- `GET /api/institutional-documents/documents/{id}/download/`
- `GET /api/institutional-documents/documents/{id}/versions/`

Review body:

```json
{
  "comment": "Approved."
}
```

New version body, multipart:

```json
{
  "version_number": "1.1",
  "change_summary": "Updated policy section."
}
```

Include `file` or `external_url` depending on version type.
