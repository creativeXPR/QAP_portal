# DQA Digital Quality Assurance Platform API Integration Guide

This document is the frontend integration reference for the currently implemented backend API. It documents only routes and behavior that exist in the current Django project.

## 1. Project Overview

### Purpose

The API supports the DQA Digital Quality Assurance Platform. It provides backend services for:

- Authentication and user roles
- Faculty and department records
- Course and lecture monitoring
- Examination quality monitoring
- Lecturer assessment
- UI-AReQuM accreditation readiness monitoring
- QA committee governance, reviews, findings, and action tracking
- Accreditation analytics dashboards
- Institutional document management

### Architecture

The backend is a Django and Django REST Framework API. Most resource endpoints use DRF ViewSets. Some modules return plain DRF serializer responses, while accreditation and institutional documents use a custom response envelope.

### Base URLs

Development:

```text
http://127.0.0.1:8000
```

Localhost alternative:

```text
http://localhost:8000
```

Staging and production base URLs are not configured in this repository.

### API Version

No explicit API version is implemented. All endpoints are currently unversioned under `/api/`.

### Content Types

Use JSON for normal requests:

```http
Content-Type: application/json
Accept: application/json
```

Use multipart form data for file uploads:

```http
Content-Type: multipart/form-data
```

### Character Encoding

Use UTF-8.

### Dates And Times

Date fields use ISO date format:

```text
YYYY-MM-DD
```

Date-time fields use ISO 8601:

```text
2026-07-07T10:00:00Z
```

The Django project timezone is `UTC`.

## 2. Authentication

### Authentication Strategy

Protected endpoints use JWT authentication. The frontend logs in, receives an access token, and sends it in the `Authorization` header.

```http
Authorization: Bearer <access_token>
```

### Main Login Endpoint

Use this endpoint for normal login:

```http
POST /api/auth/login/
```

Request:

```json
{
  "username": "demo_admin",
  "password": "StrongPass123!"
}
```

Success response:

```json
{
  "refresh": "refresh-token-string",
  "access": "access-token-string",
  "profile_complete": true,
  "user_id": 1,
  "user": {
    "id": 1,
    "username": "demo_admin",
    "email": "demo_admin@example.com",
    "full_name": "demo_admin",
    "first_name": "",
    "last_name": ""
  }
}
```

Validation errors:

```json
{
  "error": "username and password are required"
}
```

Invalid credentials:

```json
{
  "error": "Invalid credentials"
}
```

Frontend handling:

- Store the `access` token in memory or secure storage.
- Send the token with all protected requests.
- If a request returns `401`, redirect to login or ask the user to log in again.
- Current local JWT settings make access tokens valid for 60 minutes and refresh tokens valid for 7 days.
- The current URL map does not expose a dedicated token refresh endpoint, so frontend refresh behavior should not be assumed unless that route is added.

### Registration Endpoint

Custom registration endpoint:

```http
POST /api/auth/google/register/
```

Despite the path containing `google`, this endpoint creates a username/password account in the current implementation.

Request:

```json
{
  "username": "dqa_admin",
  "email": "dqa_admin@example.com",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!",
  "status": "admin"
}
```

Fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| username | string | Yes | Login username |
| email | string | Yes | User email |
| password | string | Yes | Password validated by Django password validators |
| password_confirm | string | Yes | Must match `password` |
| status | string | No | Role. Defaults to `student` |

Allowed `status` values from the profile model:

```text
student
focal_person
principle_officer
admin
```

Success response uses status code `201` and returns JWT tokens plus the user object. Registration no longer accepts separate first name or last name fields. For display, use the returned `user.full_name`, which falls back to the username when no stored name exists.

Errors:

```json
{ "error": "Username already exists" }
```

```json
{ "error": "Email already exists" }
```

```json
{ "error": "Passwords do not match" }
```

### Google Login Endpoint

```http
POST /api/auth/google/
```

Request:

```json
{
  "id_token": "google-id-token"
}
```

This validates a Google ID token against the configured Google client ID.

### Complete Profile Endpoint

```http
POST /api/auth/google/complete-profile/
```

Authentication: required.

Request:

```json
{
  "username": "dqa_admin",
  "status": "admin"
}
```

Success:

```json
{
  "message": "Profile updated successfully!",
  "username": "dqa_admin",
  "status": "admin"
}
```

### Other Auth Routes Registered From `dj-rest-auth`

These routes are registered by the installed package:

```text
POST /api/auth/login/
POST /api/auth/logout/
GET/PUT/PATCH /api/auth/user/
POST /api/auth/password/reset/
POST /api/auth/password/reset/confirm/
POST /api/auth/password/change/
POST /api/auth/registration/
POST /api/auth/registration/verify-email/
POST /api/auth/registration/resend-email/
```

For this project, frontend integration should prefer the custom login and registration endpoints documented above because they include the profile fields used by local role checks.

### Roles And Permissions

| Role | Typical Access |
|---|---|
| admin | Full management access |
| principle_officer | High-level review and publishing access |
| focal_person | Submit accreditation data and upload evidence |
| student | Normal authenticated user |
| anonymous | Public access only where explicitly allowed |

## 3. Response Shapes

### Plain DRF Response Modules

These modules use normal DRF serializer responses:

- authentication
- core
- courses
- examinations
- lecturers
- qa_committee

List example:

```json
[
  {
    "id": 1,
    "name": "Faculty of Science"
  }
]
```

Create example:

```json
{
  "id": 1,
  "name": "Faculty of Science"
}
```

### Wrapped Response Modules

These modules use a custom response envelope:

- accreditation
- analytics
- institutional documents

Success:

```json
{
  "success": true,
  "message": "Request completed successfully.",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {}
}
```

Paginated list:

```json
{
  "success": true,
  "message": "Request completed successfully.",
  "data": [],
  "pagination": {
    "count": 1,
    "next": null,
    "previous": null
  }
}
```

## 4. Core API

Core provides faculty and department records used by courses, examinations, and lecturers.

Base path:

```text
/api/core/
```

Authentication: required for all core endpoints.

### Faculty Object

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Faculty ID |
| name | string | No | Faculty name, unique |

### Department Object

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Department ID |
| faculty | integer | No | Faculty ID |
| faculty_name | string | No | Read-only faculty name |
| name | string | No | Department name |

### Faculty Endpoints

```http
GET /api/core/faculties/
POST /api/core/faculties/
GET /api/core/faculties/{id}/
PUT /api/core/faculties/{id}/
PATCH /api/core/faculties/{id}/
DELETE /api/core/faculties/{id}/
```

Search:

```http
GET /api/core/faculties/?search=science
```

Create request:

```json
{
  "name": "Faculty of Science"
}
```

### Department Endpoints

```http
GET /api/core/departments/
POST /api/core/departments/
GET /api/core/departments/{id}/
PUT /api/core/departments/{id}/
PATCH /api/core/departments/{id}/
DELETE /api/core/departments/{id}/
```

Search:

```http
GET /api/core/departments/?search=computer
```

Create request:

```json
{
  "faculty": 1,
  "name": "Computer Science"
}
```

Validation:

- Faculty name must be unique.
- Department name must be unique within the same faculty.
- `faculty` is required when creating a department.

Frontend use:

- Load faculties before creating departments.
- Load departments before creating courses, exam sessions, or lecturer profiles.

## 5. Students API

The Students API manages student academic records and student feedback. Student records integrate with core faculties/departments, courses, and authentication users.

Base path:

```text
/api/students/
```

Authentication: required.

### Student Permissions

| User role | Access |
|---|---|
| admin | Full student record access |
| principle_officer | Full student record access |
| focal_person | Create, list, retrieve, update student records |
| student | Can retrieve/list only their own linked student record |
| unauthenticated | No access |

Only `admin` and `principle_officer` can delete student records.

### Student Object

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Student record ID |
| user | integer | Yes | Optional linked authentication user ID |
| matric_number | string | No | Unique matric number |
| first_name | string | No | Student first name |
| last_name | string | No | Student last name |
| full_name | string | No | Read-only combined name |
| email | string | No | Unique student email |
| faculty | integer | No | Faculty ID |
| faculty_name | string | No | Read-only faculty name |
| department | integer | No | Department ID |
| department_name | string | No | Read-only department name |
| programme | string | No | Programme name |
| level | string | No | `100`, `200`, `300`, `400`, `500`, or `PG` |
| status | string | No | `active`, `inactive`, `suspended`, or `graduated` |
| courses | integer[] | Yes | Course IDs linked to the student |
| course_codes | string[] | No | Read-only linked course codes |
| created_at | datetime | No | Created timestamp |
| updated_at | datetime | No | Updated timestamp |

### Student Endpoints

```http
GET /api/students/
POST /api/students/
GET /api/students/{id}/
PUT /api/students/{id}/
PATCH /api/students/{id}/
DELETE /api/students/{id}/
```

Create request:

```json
{
  "user": 5,
  "matric_number": "CSC/2026/001",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@student.example.com",
  "faculty": 1,
  "department": 3,
  "programme": "BSc Computer Science",
  "level": "100",
  "status": "active",
  "courses": [10, 11]
}
```

Success response:

```json
{
  "id": 1,
  "user": 5,
  "matric_number": "CSC/2026/001",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "full_name": "Ada Lovelace",
  "email": "ada@student.example.com",
  "faculty": 1,
  "faculty_name": "Faculty of Science",
  "department": 3,
  "department_name": "Computer Science",
  "programme": "BSc Computer Science",
  "level": "100",
  "status": "active",
  "courses": [10, 11],
  "course_codes": ["CSC 101", "CSC 102"],
  "created_at": "2026-07-07T10:00:00Z",
  "updated_at": "2026-07-07T10:00:00Z"
}
```

Filters:

```http
GET /api/students/?faculty=1
GET /api/students/?department=3
GET /api/students/?level=100
GET /api/students/?status=active
GET /api/students/?courses=10
GET /api/students/?search=ada
GET /api/students/?ordering=matric_number
```

Validation:

- `matric_number` must be unique.
- `email` must be unique and valid.
- `faculty` and `department` are required.
- `department` must belong to the selected `faculty`.
- Linked `courses` must belong to the selected `department`.
- `matric_number` may contain only letters, numbers, slash, underscore, and hyphen.

### Student Complaint And Feedback Endpoints

Student complaints use the existing `StudentFeedback` resource. A student creates feedback with `category=complaint`; staff then manage the complaint lifecycle from the same endpoint.

```http
GET /api/students/feedback-tracking/
POST /api/students/feedback-tracking/
GET /api/students/feedback/
POST /api/students/feedback/
GET /api/students/feedback/{id}/
PUT /api/students/feedback/{id}/
PATCH /api/students/feedback/{id}/
DELETE /api/students/feedback/{id}/
GET /api/students/notifications/
GET /api/students/notifications/{id}/
POST /api/students/notifications/{id}/mark-read/
```

Student complaint create request:

```json
{
  "student": "student_user",
  "feedback": "Lecture room needs better ventilation.",
  "category": "complaint",
  "urgency": "high"
}
```

Create response includes the current status and timeline fields:

```json
{
  "id": 1,
  "submitted_by": 7,
  "submitted_by_username": "student_user",
  "student": "student_user",
  "student_email": null,
  "feedback": "Lecture room needs better ventilation.",
  "category": "complaint",
  "classification": "academic",
  "status": "pending",
  "urgency": "high",
  "admin_comment": "",
  "assigned_to": null,
  "assigned_to_username": null,
  "updated_by": null,
  "updated_by_username": null,
  "submitted_at": "2026-07-07T10:00:00Z",
  "updated_at": "2026-07-07T10:00:00Z",
  "updates": [],
  "notification_history": []
}
```

Allowed feedback categories:

```text
complaint
suggestion
inquiry
academic
support
other
```

Allowed urgency values:

```text
normal
high
critical
```

Complaint statuses:

```text
pending
under_review
in_progress
awaiting_student_response
resolved
closed
rejected
```

Feedback status defaults to `pending` on create. Students cannot set staff-only fields such as `status`, `admin_comment`, or `assigned_to`.

Admin/staff update request:

```http
PATCH /api/students/feedback/{id}/
```

```json
{
  "status": "under_review",
  "admin_comment": "We are reviewing this with the department.",
  "assigned_to": 3
}
```

When staff change the status, add an admin comment, reassign, resolve, or close a complaint, the backend automatically:

- updates the complaint
- records a timeline entry in `updates`
- stores `updated_by` and `updated_at`
- creates an unread notification for the student

Students can open the same complaint detail endpoint to view the current status, latest admin comment, update timeline, and notification history.

Notification list response:

```json
[
  {
    "id": 1,
    "title": "Complaint Updated",
    "message": "Your complaint is now Under Review.",
    "notification_type": "complaint_update",
    "user": 7,
    "complaint": 1,
    "complaint_id": 1,
    "is_read": false,
    "created_at": "2026-07-07T10:30:00Z"
  }
]
```

Mark notification as read:

```http
POST /api/students/notifications/{id}/mark-read/
```

## 6. Courses API

Base path:

```text
/api/courses/
```

Authentication: required.

### Course Object

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Course ID |
| code | string | No | Unique course code |
| title | string | No | Course title |
| department | integer | No | Department ID |
| department_name | string | No | Read-only department name |

### Lecture Session Object

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Lecture session ID |
| course | integer | No | Course ID |
| course_code | string | No | Read-only course code |
| department_name | string | No | Read-only department name |
| faculty_name | string | No | Read-only faculty name |
| respondent | integer | Yes | User ID, assigned automatically |
| respondent_email | string | Yes | Read-only respondent email |
| monitored_at | datetime | No | Monitoring date/time |
| time_slot | string | No | Lecture time slot |
| level | string | No | Student level |
| mode | string | No | physical, online, or hybrid |
| lecturer_present | string | No | yes, late, or no |
| actual_duration | string | No | Duration choice |
| venue | string | No | Venue |
| held | boolean | No | Whether lecture held |
| explanation | string | Yes | Optional explanation |
| reason_not_held | string | Yes | Required if held is false |
| estimated_attendance | string | No | Attendance range |
| classroom_environment_rating | integer | No | Rating 1 to 5 |
| teaching_effectiveness_rating | integer | No | Rating 1 to 5 |
| quality_concerns | string | Yes | Optional concerns |
| created_at | datetime | No | Created time |

### Course Endpoints

```http
GET /api/courses/courses/
POST /api/courses/courses/
GET /api/courses/courses/{id}/
PUT /api/courses/courses/{id}/
PATCH /api/courses/courses/{id}/
DELETE /api/courses/courses/{id}/
```

Search:

```http
GET /api/courses/courses/?search=CSC
```

Create request:

```json
{
  "department": 48,
  "code": "CSC 101",
  "title": "Introduction to Computing"
}
```

### Lecture Session Endpoints

```http
GET /api/courses/lecture-sessions/
POST /api/courses/lecture-sessions/
GET /api/courses/lecture-sessions/{id}/
PUT /api/courses/lecture-sessions/{id}/
PATCH /api/courses/lecture-sessions/{id}/
DELETE /api/courses/lecture-sessions/{id}/
```

Filters:

```http
GET /api/courses/lecture-sessions/?held=true
GET /api/courses/lecture-sessions/?mode=physical
GET /api/courses/lecture-sessions/?level=100
GET /api/courses/lecture-sessions/?course=1
GET /api/courses/lecture-sessions/?search=CSC
```

Create request:

```json
{
  "course": 1,
  "monitored_at": "2026-07-07T10:00:00Z",
  "time_slot": "10:00-11:00",
  "level": "100",
  "mode": "physical",
  "lecturer_present": "yes",
  "actual_duration": "45-60",
  "venue": "Room A",
  "held": true,
  "explanation": "",
  "reason_not_held": "",
  "estimated_attendance": "100-500",
  "classroom_environment_rating": 4,
  "teaching_effectiveness_rating": 5,
  "quality_concerns": ""
}
```

Validation:

- `reason_not_held` is required when `held` is false.
- `reason_not_held` must be blank when `held` is true.
- Ratings must be between 1 and 5.
- Respondent is assigned from the logged-in user.

Frontend use:

- Course monitoring form should call this endpoint after user selects course, level, time slot, and enters ratings.
- If `held=false`, show and require the reason field.

## 7. Examinations API

Base path:

```text
/api/examinations/
```

Authentication: required.

### Exam Session Object

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Exam session ID |
| department | integer | No | Department ID |
| department_name | string | No | Read-only department name |
| faculty_name | string | No | Read-only faculty name |
| course_code_title | string | No | Course code/title text |
| exam_date | date | No | Exam date |
| venue | string | No | Exam venue |
| academic_session | string | No | Academic session |

### Exam Quality Report Object

All rating fields are integers from 1 to 5.

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Report ID |
| exam_session | integer | No | Exam session ID |
| course_code_title | string | No | Read-only course text |
| student | integer | Yes | Assigned automatically from logged-in user |
| adequacy_of_seating | integer | No | Rating 1 to 5 |
| lighting_conditions | integer | No | Rating 1 to 5 |
| ventilation_room_comfort | integer | No | Rating 1 to 5 |
| noise_free_environment | integer | No | Rating 1 to 5 |
| accessibility_suitability_of_venue | integer | No | Rating 1 to 5 |
| invigilators_arrived_on_time | integer | No | Rating 1 to 5 |
| clear_communication_of_instructions | integer | No | Rating 1 to 5 |
| professional_conduct_of_invigilators | integer | No | Rating 1 to 5 |
| fair_consistent_enforcement_of_rules | integer | No | Rating 1 to 5 |
| responsiveness_to_student_needs | integer | No | Rating 1 to 5 |
| prompt_start_of_examination | integer | No | Rating 1 to 5 |
| organized_distribution_of_materials | integer | No | Rating 1 to 5 |
| proper_management_of_exam_time | integer | No | Rating 1 to 5 |
| orderliness_during_submission | integer | No | Rating 1 to 5 |
| provision_for_special_needs | integer | Yes | Optional rating 1 to 5 |
| observed_misconduct | boolean | No | Whether misconduct was observed |
| incident_description | string | Yes | Required if misconduct observed |
| action_taken | string | Yes | Optional action taken |
| overall_rating | integer | No | Rating 1 to 5 |
| suggestions_for_improvement | string | Yes | Optional suggestions |
| submitted_at | datetime | No | Submission time |

### Exam Session Endpoints

```http
GET /api/examinations/exam-sessions/
POST /api/examinations/exam-sessions/
GET /api/examinations/exam-sessions/{id}/
PUT /api/examinations/exam-sessions/{id}/
PATCH /api/examinations/exam-sessions/{id}/
DELETE /api/examinations/exam-sessions/{id}/
```

Search:

```http
GET /api/examinations/exam-sessions/?search=CSC
```

Create request:

```json
{
  "department": 48,
  "course_code_title": "CSC 101 - Introduction to Computing",
  "exam_date": "2026-07-20",
  "venue": "Hall A",
  "academic_session": "First Semester 2026/2027"
}
```

### Exam Quality Report Endpoints

```http
GET /api/examinations/quality-reports/
POST /api/examinations/quality-reports/
GET /api/examinations/quality-reports/{id}/
PUT /api/examinations/quality-reports/{id}/
PATCH /api/examinations/quality-reports/{id}/
DELETE /api/examinations/quality-reports/{id}/
```

Filters:

```http
GET /api/examinations/quality-reports/?exam_session=1
GET /api/examinations/quality-reports/?observed_misconduct=false
GET /api/examinations/quality-reports/?search=CSC
```

Create request:

```json
{
  "exam_session": 1,
  "adequacy_of_seating": 4,
  "lighting_conditions": 4,
  "ventilation_room_comfort": 4,
  "noise_free_environment": 5,
  "accessibility_suitability_of_venue": 4,
  "invigilators_arrived_on_time": 5,
  "clear_communication_of_instructions": 4,
  "professional_conduct_of_invigilators": 5,
  "fair_consistent_enforcement_of_rules": 4,
  "responsiveness_to_student_needs": 4,
  "prompt_start_of_examination": 5,
  "organized_distribution_of_materials": 4,
  "proper_management_of_exam_time": 5,
  "orderliness_during_submission": 4,
  "provision_for_special_needs": 4,
  "observed_misconduct": false,
  "incident_description": "",
  "action_taken": "",
  "overall_rating": 4,
  "suggestions_for_improvement": "Maintain current standard."
}
```

Validation:

- Rating fields must be 1 to 5.
- `incident_description` is required when `observed_misconduct=true`.
- Student is assigned from the logged-in user.

## 8. Lecturers API

Base path:

```text
/api/lecturers/
```

Authentication: required.

### Lecturer Profile Object

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Lecturer profile ID |
| user | integer | No | User ID |
| full_name | string | Yes | Read-only user full name |
| department | integer | No | Department ID |
| department_name | string | No | Read-only department name |
| faculty_name | string | No | Read-only faculty name |
| staff_id | string | No | Unique staff ID |
| rank | string | Yes | Lecturer rank |

### Assessment Report Object

All indicator fields are ratings from 1 to 5.

| Field | Type | Nullable | Description |
|---|---|---:|---|
| id | integer | No | Assessment ID |
| lecturer | integer | No | Lecturer profile ID |
| lecturer_name | string | Yes | Read-only lecturer name |
| student | integer | Yes | Assigned automatically |
| course | integer | No | Course ID |
| course_code | string | No | Read-only course code |
| academic_session | string | No | Academic session |
| semester | string | Yes | Semester |
| presents_content_actively | integer | No | Rating 1 to 5 |
| covers_content_within_timeframe | integer | No | Rating 1 to 5 |
| gives_useful_assignments | integer | No | Rating 1 to 5 |
| impressive_comportment | integer | No | Rating 1 to 5 |
| punctual_at_lectures | integer | No | Rating 1 to 5 |
| available_for_consultation | integer | No | Rating 1 to 5 |
| clear_on_concepts | integer | No | Rating 1 to 5 |
| links_theory_to_practice | integer | No | Rating 1 to 5 |
| encourages_participation | integer | No | Rating 1 to 5 |
| provides_assignment_feedback | integer | No | Rating 1 to 5 |
| teaches_per_course_outline | integer | No | Rating 1 to 5 |
| teaches_class_regularly | integer | No | Rating 1 to 5 |
| updates_course_content | integer | No | Rating 1 to 5 |
| uses_real_life_examples | integer | No | Rating 1 to 5 |
| appears_neatly | integer | No | Rating 1 to 5 |
| uses_varied_teaching_methods | integer | No | Rating 1 to 5 |
| uses_technology_innovatively | integer | No | Rating 1 to 5 |
| average_rating | number | No | Read-only computed average |
| included_in_dossier | boolean | No | Read-only in API serializer |
| submitted_at | datetime | No | Submission time |

### Lecturer Profile Endpoints

```http
GET /api/lecturers/lecturer-profiles/
POST /api/lecturers/lecturer-profiles/
GET /api/lecturers/lecturer-profiles/{id}/
PUT /api/lecturers/lecturer-profiles/{id}/
PATCH /api/lecturers/lecturer-profiles/{id}/
DELETE /api/lecturers/lecturer-profiles/{id}/
GET /api/lecturers/lecturer-profiles/{id}/assessment_summary/
```

Search:

```http
GET /api/lecturers/lecturer-profiles/?search=demo_lecturer
```

Create request:

```json
{
  "user": 2,
  "department": 48,
  "staff_id": "DEMO-LECT-001",
  "rank": "Senior Lecturer"
}
```

Assessment summary response:

```json
{
  "total_assessments": 1,
  "overall_average": 4.0,
  "by_course": [
    {
      "course__code": "CSC 101",
      "avg": 4.0
    }
  ]
}
```

### Assessment Report Endpoints

```http
GET /api/lecturers/assessment-reports/
POST /api/lecturers/assessment-reports/
GET /api/lecturers/assessment-reports/{id}/
PUT /api/lecturers/assessment-reports/{id}/
PATCH /api/lecturers/assessment-reports/{id}/
DELETE /api/lecturers/assessment-reports/{id}/
```

Filters:

```http
GET /api/lecturers/assessment-reports/?lecturer=1
GET /api/lecturers/assessment-reports/?course=1
GET /api/lecturers/assessment-reports/?academic_session=2026/2027
GET /api/lecturers/assessment-reports/?semester=First
GET /api/lecturers/assessment-reports/?included_in_dossier=false
GET /api/lecturers/assessment-reports/?search=CSC
```

Create request:

```json
{
  "lecturer": 1,
  "course": 1,
  "academic_session": "2026/2027",
  "semester": "First",
  "presents_content_actively": 4,
  "covers_content_within_timeframe": 4,
  "gives_useful_assignments": 4,
  "impressive_comportment": 4,
  "punctual_at_lectures": 4,
  "available_for_consultation": 4,
  "clear_on_concepts": 4,
  "links_theory_to_practice": 4,
  "encourages_participation": 4,
  "provides_assignment_feedback": 4,
  "teaches_per_course_outline": 4,
  "teaches_class_regularly": 4,
  "updates_course_content": 4,
  "uses_real_life_examples": 4,
  "appears_neatly": 4,
  "uses_varied_teaching_methods": 4,
  "uses_technology_innovatively": 4
}
```

Validation:

- Every indicator rating must be 1 to 5.
- Student is assigned from the logged-in user.

## 9. Accreditation API

Base path:

```text
/api/accreditation/
```

Authentication: required.

Response shape: wrapped response envelope.

### Accreditation Roles

| Role | Access |
|---|---|
| admin, staff, superuser, principle_officer | Full access |
| focal_person | Submission and selected update actions |
| authenticated user | Read-only |
| anonymous | Denied |

### Accreditation Objects

Important objects:

- AccreditationCycle
- AccreditationComponent
- AccreditationMetric
- MetricSubmission
- Evidence
- ComponentScore
- PARIResult
- RiskClassification
- EarlyWarningAlert
- CorrectiveAction

### Cycle Endpoints

```http
GET /api/accreditation/cycles/
POST /api/accreditation/cycles/
GET /api/accreditation/cycles/{id}/
PUT /api/accreditation/cycles/{id}/
PATCH /api/accreditation/cycles/{id}/
DELETE /api/accreditation/cycles/{id}/
PATCH /api/accreditation/cycles/{id}/close/
```

Create request:

```json
{
  "title": "2026 NUC Readiness",
  "academic_session": "2026/2027",
  "semester": "First",
  "accreditation_body": "NUC",
  "accreditation_type": "Full",
  "faculty": "Faculty of Science",
  "department": "Computer Science",
  "programme": "BSc Computer Science",
  "start_date": "2026-07-01",
  "submission_deadline": "2026-08-15",
  "internal_review_deadline": "2026-08-30",
  "external_visit_date": "2026-10-10",
  "status": "submission_open"
}
```

Status values:

```text
draft
active
submission_open
internal_review
correction_required
ready_for_visit
external_visit_completed
final_report_approved
closed
```

### Components And Metrics

```http
GET /api/accreditation/components/
POST /api/accreditation/components/
GET /api/accreditation/components/{id}/
PATCH /api/accreditation/components/{id}/

GET /api/accreditation/metrics/
POST /api/accreditation/metrics/
GET /api/accreditation/metrics/{id}/
PATCH /api/accreditation/metrics/{id}/
```

Useful calls:

```http
GET /api/accreditation/components/
GET /api/accreditation/metrics/?component=curriculum_delivery
```

Calling components or metrics ensures default UI-AReQuM components and metrics exist.

### Bulk Submission

```http
POST /api/accreditation/submissions/bulk/
```

Request:

```json
{
  "cycle": 1,
  "programme": "BSc Computer Science",
  "component": "curriculum_delivery",
  "source_unit": "Departmental QA Focal Person",
  "reporting_period": "2026-Q3",
  "responses": [
    { "metric": "lectures_scheduled", "numeric_value": 120 },
    { "metric": "lectures_held", "numeric_value": 108 },
    { "metric": "topics_planned", "numeric_value": 64 },
    { "metric": "topics_completed", "numeric_value": 58 }
  ]
}
```

Validation:

- `cycle` must exist.
- `component` must exist.
- Each metric must belong to the selected component.
- At least one value field must be supplied per response.
- Numeric values must not be negative.
- Duplicate submissions for same cycle/programme/component/metric/reporting period are updated.

### Evidence

```http
GET /api/accreditation/evidence/
POST /api/accreditation/evidence/
GET /api/accreditation/evidence/{id}/
PATCH /api/accreditation/evidence/{id}/
PATCH /api/accreditation/evidence/{id}/verify/
PATCH /api/accreditation/evidence/{id}/reject/
```

Multipart create fields:

```text
cycle=1
programme=BSc Computer Science
component=2
metric=18
title=Course Outline
evidence_type=course_outline
file=<binary file>
```

Verify request:

```json
{
  "reviewer_comment": "Evidence verified."
}
```

Reject request:

```json
{
  "reviewer_comment": "Please replace file.",
  "rejection_reason": "Unsigned copy"
}
```

Evidence statuses:

```text
missing
uploaded
under_review
verified
rejected
replacement_required
```

### Component Score Calculation

```http
POST /api/accreditation/cycles/{cycle_id}/programmes/{programme_id}/calculate-component-scores/
```

Example:

```http
POST /api/accreditation/cycles/1/programmes/BSc%20Computer%20Science/calculate-component-scores/
```

Request body:

```json
{}
```

Success:

```json
{
  "success": true,
  "message": "Component scores calculated.",
  "data": {
    "programme": "BSc Computer Science",
    "cycle": 1,
    "scores": [
      {
        "component": "curriculum_delivery",
        "score": 100.0,
        "status": "good",
        "metrics": {
          "lecture_delivery_rate": 90.0,
          "course_coverage": 90.63
        }
      }
    ]
  }
}
```

### PARI Calculation

```http
POST /api/accreditation/cycles/{cycle_id}/programmes/{programme_id}/calculate-pari/
```

PARI classifications:

```text
80-100: accreditation_ready
60-79: moderate_risk
below 60: high_risk
```

Success:

```json
{
  "success": true,
  "message": "PARI calculated.",
  "data": {
    "programme": "BSc Computer Science",
    "cycle": 1,
    "pari_score": 74.2,
    "classification": "moderate_risk",
    "breakdown": [
      {
        "component": "staffing",
        "weight": 25.0,
        "score": 70.0,
        "weighted_score": 17.5
      }
    ],
    "alerts_created": 1
  }
}
```

### Alerts

```http
GET /api/accreditation/alerts/
POST /api/accreditation/alerts/
GET /api/accreditation/alerts/{id}/
PATCH /api/accreditation/alerts/{id}/
PATCH /api/accreditation/alerts/{id}/acknowledge/
PATCH /api/accreditation/alerts/{id}/resolve/
PATCH /api/accreditation/alerts/{id}/escalate/
```

Alert statuses:

```text
open
acknowledged
in_progress
resolved
escalated
```

Severities:

```text
low
medium
high
critical
```

### Corrective Actions

```http
GET /api/accreditation/actions/
POST /api/accreditation/actions/
GET /api/accreditation/actions/{id}/
PATCH /api/accreditation/actions/{id}/
PATCH /api/accreditation/actions/{id}/progress/
PATCH /api/accreditation/actions/{id}/submit/
PATCH /api/accreditation/actions/{id}/verify/
PATCH /api/accreditation/actions/{id}/reject/
PATCH /api/accreditation/actions/{id}/close/
```

Create request:

```json
{
  "cycle": 1,
  "programme": "BSc Computer Science",
  "component": 1,
  "alert": 5,
  "title": "Recruit adjunct lecturers",
  "description": "Close the immediate staffing gap before internal review.",
  "assigned_unit": "Department of Computer Science",
  "responsible_officer": "HOD",
  "priority": "high",
  "deadline": "2026-08-20"
}
```

Progress request:

```json
{
  "progress_percentage": 60,
  "reviewer_comment": "Recruitment memo submitted."
}
```

Validation:

- Progress must be between 0 and 100.

### Accreditation Filters

Supported where applicable:

```text
cycle
programme
faculty
department
component
status
risk_classification
reporting_period
date_from
date_to
```

Example:

```http
GET /api/accreditation/actions/?cycle=1&component=staffing&status=in_progress
```

## 10. Analytics API

Base path:

```text
/api/analytics/accreditation/
```

Authentication: required.

Response shape: wrapped response envelope.

### Endpoints

```http
GET /api/analytics/accreditation/overview/
GET /api/analytics/accreditation/programmes-by-risk/
GET /api/analytics/accreditation/component-performance/
GET /api/analytics/accreditation/early-warning/
GET /api/analytics/accreditation/faculty-summary/
GET /api/analytics/accreditation/department-summary/
GET /api/analytics/accreditation/timeline/
```

Supported filters on PARI-based analytics:

```text
cycle
faculty
department
programme
risk_classification
```

Overview response:

```json
{
  "success": true,
  "message": "Analytics fetched successfully.",
  "data": {
    "total_programmes_monitored": 1,
    "accreditation_ready_count": 0,
    "moderate_risk_count": 1,
    "high_risk_count": 0,
    "average_pari_score": 74.2,
    "open_alerts": 3,
    "overdue_actions": 0,
    "evidence_completion_rate": 50.0,
    "timely_submission_rate": 100.0
  }
}
```

Frontend use:

- Dashboard home should call overview first.
- Risk chart should call programmes-by-risk.
- Component chart should call component-performance.
- Alert dashboard should call early-warning.

## 11. QA Committee API

The QA Committee API manages committee governance records. It does not copy raw operational data from accreditation, courses, examinations, documents, students, or analytics. Instead, committee records can reference those modules through review summaries, findings, recommendations, action plans, evidence, and reports.

Base path:

```text
/api/qa-committee/
```

Authentication: required.

Response shape: plain DRF serializer responses.

### QA Committee Permissions

| Role | Access |
|---|---|
| super_admin, dqa_admin, admin, principle_officer | Manage all committee records |
| committee_chairperson, committee_secretary, qa_focal_person, focal_person | Manage committee workflows where permitted |
| committee_member, department_admin, faculty_admin, read_only_viewer | View or contribute within allowed committee context |
| student | Blocked from committee governance endpoints |
| unauthenticated | No access |

Evidence verification is restricted to admins, QA focal persons, committee chairpersons, and committee secretaries.

### Committee Endpoints

```http
GET /api/qa-committee/committees/
POST /api/qa-committee/committees/
GET /api/qa-committee/committees/{id}/
PUT /api/qa-committee/committees/{id}/
PATCH /api/qa-committee/committees/{id}/
DELETE /api/qa-committee/committees/{id}/
GET /api/qa-committee/committees/{id}/members/
POST /api/qa-committee/committees/{id}/members/
GET /api/qa-committee/committees/{id}/dashboard/
```

Create committee request:

```json
{
  "name": "Faculty of Science QA Committee",
  "scope_type": "faculty",
  "faculty": 1,
  "department": null,
  "programme": "",
  "description": "Faculty-level quality assurance oversight committee.",
  "status": "active",
  "date_constituted": "2026-07-07"
}
```

Validation:

- `department` is required when `scope_type=department`.
- `faculty` is required when `scope_type=faculty`.
- `programme` is required when `scope_type=programme`.
- Department must belong to the selected faculty.
- Duplicate active committees for the same scope are rejected.

### Member Endpoints

```http
GET /api/qa-committee/members/
POST /api/qa-committee/members/
GET /api/qa-committee/members/{id}/
PATCH /api/qa-committee/members/{id}/
DELETE /api/qa-committee/members/{id}/
```

Create member request:

```json
{
  "committee": 1,
  "user": 5,
  "role": "chairperson",
  "designation": "Dean",
  "start_date": "2026-07-07",
  "end_date": null,
  "is_active": true
}
```

Allowed roles:

```text
chairperson
secretary
member
qa_focal_person
observer
```

Validation:

- Only one active chairperson is allowed per committee.
- Only one active secretary is allowed per committee.
- A user cannot be added twice to the same committee.

### Meeting And Attendance Endpoints

```http
GET /api/qa-committee/meetings/
POST /api/qa-committee/meetings/
GET /api/qa-committee/meetings/{id}/
PATCH /api/qa-committee/meetings/{id}/
DELETE /api/qa-committee/meetings/{id}/
POST /api/qa-committee/meetings/{id}/mark-held/
POST /api/qa-committee/meetings/{id}/attendance/
GET /api/qa-committee/attendance/
POST /api/qa-committee/attendance/
GET /api/qa-committee/attendance/{id}/
PATCH /api/qa-committee/attendance/{id}/
DELETE /api/qa-committee/attendance/{id}/
```

Create meeting request:

```json
{
  "committee": 1,
  "title": "Quarterly QA Review",
  "meeting_type": "quarterly_review",
  "scheduled_date": "2026-07-14T10:00:00Z",
  "venue": "Faculty Board Room",
  "agenda": "Review findings and action plan progress.",
  "minutes": "",
  "status": "scheduled"
}
```

Bulk attendance request:

```json
{
  "attendance": [
    {
      "member": 1,
      "attendance_status": "present",
      "remarks": ""
    }
  ]
}
```

### Audit Cycle And Finding Endpoints

```http
GET /api/qa-committee/audit-cycles/
POST /api/qa-committee/audit-cycles/
GET /api/qa-committee/audit-cycles/{id}/
PATCH /api/qa-committee/audit-cycles/{id}/
DELETE /api/qa-committee/audit-cycles/{id}/
POST /api/qa-committee/audit-cycles/{id}/submit/
POST /api/qa-committee/audit-cycles/{id}/close/
GET /api/qa-committee/findings/
POST /api/qa-committee/findings/
GET /api/qa-committee/findings/{id}/
PATCH /api/qa-committee/findings/{id}/
DELETE /api/qa-committee/findings/{id}/
POST /api/qa-committee/findings/{id}/resolve/
POST /api/qa-committee/findings/{id}/dismiss/
```

Create audit cycle request:

```json
{
  "committee": 1,
  "title": "2026 First Quarter Review",
  "review_period_start": "2026-01-01",
  "review_period_end": "2026-03-31",
  "audit_type": "accreditation_readiness",
  "target_faculty": 1,
  "target_department": 3,
  "target_programme": "BSc Computer Science",
  "status": "draft"
}
```

Create finding request:

```json
{
  "audit_cycle": 1,
  "source_module": "accreditation",
  "source_record_type": "EarlyWarningAlert",
  "source_record_id": "12",
  "title": "Critical staffing gap",
  "description": "Academic staff strength is below benchmark.",
  "category": "staffing",
  "severity": "critical",
  "risk_level": "high",
  "evidence_summary": "Referenced from accreditation early warning alert.",
  "status": "open"
}
```

`finding_code` is generated by the backend.

### Recommendation, Action Plan, And Evidence Endpoints

```http
GET /api/qa-committee/recommendations/
POST /api/qa-committee/recommendations/
GET /api/qa-committee/recommendations/{id}/
PATCH /api/qa-committee/recommendations/{id}/
DELETE /api/qa-committee/recommendations/{id}/
POST /api/qa-committee/recommendations/{id}/accept/
POST /api/qa-committee/recommendations/{id}/mark-in-progress/
POST /api/qa-committee/recommendations/{id}/mark-implemented/
POST /api/qa-committee/recommendations/{id}/verify/
GET /api/qa-committee/action-plans/
POST /api/qa-committee/action-plans/
GET /api/qa-committee/action-plans/{id}/
PATCH /api/qa-committee/action-plans/{id}/
DELETE /api/qa-committee/action-plans/{id}/
POST /api/qa-committee/action-plans/{id}/submit-evidence/
GET /api/qa-committee/evidence/
POST /api/qa-committee/evidence/
GET /api/qa-committee/evidence/{id}/
PATCH /api/qa-committee/evidence/{id}/
DELETE /api/qa-committee/evidence/{id}/
POST /api/qa-committee/evidence/{id}/verify/
POST /api/qa-committee/evidence/{id}/reject/
```

Create recommendation request:

```json
{
  "finding": 1,
  "audit_cycle": 1,
  "title": "Recruit additional lecturers",
  "recommendation_text": "Department should recruit or assign qualified academic staff.",
  "responsible_unit_type": "department",
  "responsible_faculty": 1,
  "responsible_department": 3,
  "assigned_to": 6,
  "priority": "urgent",
  "due_date": "2026-08-31",
  "status": "pending"
}
```

Create action plan request:

```json
{
  "recommendation": 1,
  "action_description": "Submit recruitment memo and workload redistribution plan.",
  "owner": 6,
  "expected_completion_date": "2026-08-15",
  "progress_percentage": 25,
  "status": "in_progress",
  "implementation_notes": "Draft memo prepared."
}
```

Submit evidence request:

```json
{
  "title": "Recruitment memo link",
  "description": "Evidence for staffing action plan.",
  "external_url": "https://example.com/recruitment-memo"
}
```

For file evidence, use multipart form data with `file=<uploaded file>`. Either `file` or `external_url` is required.

### Report And Data Review Endpoints

```http
GET /api/qa-committee/reports/
POST /api/qa-committee/reports/
GET /api/qa-committee/reports/{id}/
PATCH /api/qa-committee/reports/{id}/
DELETE /api/qa-committee/reports/{id}/
POST /api/qa-committee/reports/{id}/submit/
POST /api/qa-committee/reports/{id}/approve/
GET /api/qa-committee/data-reviews/
POST /api/qa-committee/data-reviews/
GET /api/qa-committee/data-reviews/{id}/
PATCH /api/qa-committee/data-reviews/{id}/
DELETE /api/qa-committee/data-reviews/{id}/
POST /api/qa-committee/data-reviews/{id}/validate/
POST /api/qa-committee/data-reviews/{id}/flag/
```

Create report request:

```json
{
  "committee": 1,
  "audit_cycle": 1,
  "report_type": "quarterly",
  "reporting_period_start": "2026-01-01",
  "reporting_period_end": "2026-03-31",
  "summary": "Quarterly QA committee review summary.",
  "key_findings": "Staffing and document gaps were reviewed.",
  "recommendations_summary": "Three recommendations were issued.",
  "action_plan_summary": "Two action plans are in progress.",
  "status": "draft"
}
```

Submitting a report calculates and stores `qacei_score`.

Create data review request:

```json
{
  "committee": 1,
  "review_title": "Lecture delivery data review",
  "source_module": "courses",
  "source_endpoint_or_model": "LectureSession",
  "target_faculty": 1,
  "target_department": 3,
  "target_programme": "BSc Computer Science",
  "review_period_start": "2026-01-01",
  "review_period_end": "2026-03-31",
  "extracted_summary": {
    "scheduled_lectures": 25,
    "held_lectures": 21,
    "delivery_rate": 84
  },
  "validation_status": "pending",
  "reviewer_comment": ""
}
```

### Summary And Dashboard Endpoints

```http
GET /api/qa-committee/summary/
GET /api/qa-committee/effectiveness/
GET /api/qa-committee/overdue-actions/
GET /api/qa-committee/risk-summary/
GET /api/qa-committee/activity-feed/?limit=20
GET /api/qa-committee/committees/{id}/dashboard/
```

Returned metrics include total committees, active committees, held meetings, open findings, critical findings, pending and overdue recommendations, action plan completion rate, evidence pending verification, and QACEI.

QACEI means `QA Committee Effectiveness Index`. It is scored from 0 to 5 using five criteria:

- Committee is constituted.
- At least one meeting was held.
- A report was submitted, reviewed, or approved.
- Findings were created.
- Action plans are being tracked or implemented.

### QA Committee Workflow

```text
Create committee
Add members
Schedule meeting
Mark meeting as held
Record attendance
Create audit cycle
Create findings, optionally referencing other module records
Create recommendations
Create action plans
Upload or link evidence
Verify or reject evidence
Submit committee report
View committee dashboard and QACEI
```

## 12. Dashboards API

The Dashboard API is a read-heavy reporting layer. It does not own operational QA records. It reads from existing modules such as core, accreditation, courses, examinations, documents, students, and analytics, then returns frontend-ready KPI cards, charts, alerts, and recent activity.

Base path:

```text
/api/dashboards/
```

Authentication: required.

Permissions:

- `admin`, `principle_officer`, `focal_person`, Django staff, and Django superusers can access dashboards.
- Expanded dashboard roles such as `dqa_admin`, `super_admin`, `qa_focal_person`, `committee_*`, `department_admin`, `faculty_admin`, and `read_only_viewer` are recognized if assigned in the profile status field.
- `department_admin` must pass a matching `department_id` filter tied to their linked student record.
- `faculty_admin` must pass a matching `faculty_id` filter tied to their linked student record.
- Normal `student` users are blocked from management dashboards.

### Common Query Parameters

All dashboard endpoints support these filters where the source data has compatible fields:

| Parameter | Description |
|---|---|
| faculty_id | Filter by core faculty ID |
| department_id | Filter by core department ID |
| programme_id | Filter by programme name/id where available |
| committee_id | Reserved for QA committee data |
| start_date | Start date in `YYYY-MM-DD` |
| end_date | End date in `YYYY-MM-DD` |
| period | `this_week`, `this_month`, `this_quarter`, or `this_year` |
| status | Filter by status where supported |
| risk_level | Accreditation risk classification |
| severity | Alert severity |
| limit | Activity/feed limit. Default `20`, maximum `100` |

### Response Shape

Dashboard endpoints use a consistent wrapper:

```json
{
  "success": true,
  "message": "Dashboard data fetched successfully.",
  "data": {}
}
```

When a dependency is not implemented or unavailable, the endpoint returns a safe module status instead of a server error:

```json
{
  "module": "example_dependency",
  "status": "module_not_available",
  "message": "Required source data is not available.",
  "data": []
}
```

### Dashboard Endpoints

```http
GET /api/dashboards/summary/
GET /api/dashboards/university-overview/
GET /api/dashboards/accreditation/
GET /api/dashboards/qa-committee/
GET /api/dashboards/teaching-learning/
GET /api/dashboards/examinations/
GET /api/dashboards/documents/
GET /api/dashboards/student-experience/
GET /api/dashboards/infrastructure-labs/
GET /api/dashboards/research/
GET /api/dashboards/early-warning/
GET /api/dashboards/activity-feed/
```

### Summary Dashboard

Use this endpoint for the frontend landing dashboard:

```http
GET /api/dashboards/summary/
```

Returns:

- `kpi_cards`
- `charts`
- `alerts`
- `recent_activity`
- `quick_links`

Example response:

```json
{
  "success": true,
  "message": "Dashboard data fetched successfully.",
  "data": {
    "filters": {
      "faculty_id": null,
      "department_id": null,
      "programme_id": null,
      "start_date": null,
      "end_date": null
    },
    "kpi_cards": [
      {
        "key": "average_pari",
        "label": "Average PARI Score",
        "value": 82.0,
        "unit": "%",
        "status": "good",
        "change": null
      }
    ],
    "charts": {
      "risk_distribution": {
        "type": "pie",
        "labels": ["accreditation_ready", "moderate_risk", "high_risk"],
        "datasets": [
          {
            "label": "Programmes",
            "data": [1, 0, 0]
          }
        ]
      }
    },
    "alerts": [],
    "recent_activity": [],
    "quick_links": []
  }
}
```

### University Overview

```http
GET /api/dashboards/university-overview/
```

Returns top-level QA health:

- total faculties
- total departments
- total programmes
- accreditation ready, moderate risk, and high risk programme counts
- average PARI score
- active QA committees
- average QACEI score
- open critical findings
- overdue recommendations
- pending evidence verifications
- recent accreditation alerts
- recent QA activities

### Accreditation Dashboard

```http
GET /api/dashboards/accreditation/
```

Returns:

- readiness distribution
- average readiness score
- PARI scores by programme
- PARI scores by faculty
- weakest and strongest accreditation components
- programmes on watch list
- programmes at risk
- trend over time
- missing or unverified evidence

Chart keys:

```text
readiness_distribution_pie
pari_by_programme_bar
pari_by_faculty_bar
risk_trend_line
component_score_radar_or_bar
```

### QA Committee Dashboard

```http
GET /api/dashboards/qa-committee/
```

Reads from the implemented `qa_committee` module and returns:

- total committees
- active committees
- meetings held
- reports submitted and pending
- open and critical findings
- pending, implemented, and overdue recommendations
- action plan completion rate
- evidence pending verification
- average QACEI score
- chart-ready QACEI, findings, recommendation, and action-plan datasets

### Teaching And Learning Dashboard

```http
GET /api/dashboards/teaching-learning/
```

Reads from `courses.Course` and `courses.LectureSession`.

Returns:

- total courses
- scheduled lectures
- lectures held
- average lecture delivery rate
- lecturer punctuality
- low-performing departments
- chart-ready lecture delivery datasets

### Examination Dashboard

```http
GET /api/dashboards/examinations/
```

Reads from `examinations.ExamSession` and `examinations.ExamQualityReport`.

Returns:

- total exam sessions
- quality reports submitted
- average administration, invigilation, environment, and overall scores
- malpractice cases
- malpractice rate
- unresolved exam issues
- chart-ready exam datasets

### Documents Dashboard

```http
GET /api/dashboards/documents/
```

Reads from institutional documents.

Returns:

- total documents
- documents by category
- required, submitted, and missing document counts
- pending review, approved, and rejected document counts
- expiring documents
- document completeness percentage
- chart-ready document datasets

### Student Experience Dashboard

```http
GET /api/dashboards/student-experience/
```

Reads from student feedback records.

Returns:

- total feedback responses
- total, resolved, and pending complaints
- complaint resolution rate
- zero-valued satisfaction fields where no source rating metric exists
- chart-ready feedback datasets

Private student complaint details are not exposed in dashboard summaries.

### Infrastructure, Laboratory, And Research Dashboards

```http
GET /api/dashboards/infrastructure-labs/
GET /api/dashboards/research/
```

These endpoints read from accreditation component scores where available. If no matching component scores exist, they return zeroed metrics and empty chart datasets.

### Early Warning Dashboard

```http
GET /api/dashboards/early-warning/
```

Returns:

- accreditation secure, watch list, and risk counts
- high-risk programmes
- high-risk departments
- risk drivers
- recent alerts
- alert severity distribution
- recommended corrective actions
- risk charts

### Activity Feed

```http
GET /api/dashboards/activity-feed/?limit=20
```

Returns a list of recent QA activities from available modules.

Example item:

```json
{
  "id": "alert-1",
  "type": "accreditation_alert",
  "title": "Staffing below benchmark",
  "description": "BSc Computer Science",
  "module": "accreditation",
  "severity": "critical",
  "created_at": "2026-07-07T10:00:00Z",
  "actor": null
}
```

Frontend integration notes:

- Use `/api/dashboards/summary/` for the landing dashboard.
- Use `/api/dashboards/accreditation/` for accreditation charts.
- Use `/api/dashboards/qa-committee/` for committee performance, QACEI, findings, recommendations, evidence, and action-plan metrics.
- Use `/api/dashboards/early-warning/` for risk monitoring.
- The frontend should render dashboard values returned by the API instead of recalculating institutional metrics.

## 13. Institutional Documents API

Base path:

```text
/api/institutional-documents/
```

Response shape: wrapped response envelope.

### Category Endpoints

```http
GET /api/institutional-documents/categories/
POST /api/institutional-documents/categories/
GET /api/institutional-documents/categories/{id}/
PATCH /api/institutional-documents/categories/{id}/
DELETE /api/institutional-documents/categories/{id}/
```

Create request:

```json
{
  "name": "Policy Documents",
  "description": "Official policy documents.",
  "is_active": true
}
```

`slug` is optional. If omitted, the backend generates it from `name`.

Delete deactivates the category instead of hard deletion.

### Document Endpoints

```http
GET /api/institutional-documents/documents/
POST /api/institutional-documents/documents/
GET /api/institutional-documents/documents/{id}/
PATCH /api/institutional-documents/documents/{id}/
DELETE /api/institutional-documents/documents/{id}/
POST /api/institutional-documents/documents/{id}/submit-for-review/
POST /api/institutional-documents/documents/{id}/approve/
POST /api/institutional-documents/documents/{id}/reject/
POST /api/institutional-documents/documents/{id}/publish/
POST /api/institutional-documents/documents/{id}/archive/
POST /api/institutional-documents/documents/{id}/new-version/
GET /api/institutional-documents/documents/{id}/preview/
GET /api/institutional-documents/documents/{id}/download/
GET /api/institutional-documents/documents/{id}/versions/
```

### Version And Access Log Endpoints

```http
GET /api/institutional-documents/versions/
GET /api/institutional-documents/versions/{id}/
GET /api/institutional-documents/access-logs/
GET /api/institutional-documents/access-logs/{id}/
```

### Document Types

```text
pdf
word
powerpoint
spreadsheet
image
link
other
```

### Related Modules

```text
general_dqa
accreditation
qa_committee
student_assessment
examination_quality
student_complaints
lecture_monitoring
service_delivery
institutional_policy
platform_documentation
```

### Visibility Levels

```text
private
dqa_only
qa_focal_persons
hods_and_deans
committee_members
all_authenticated
public
```

### File Document Upload

Use multipart form data:

```text
title=Quality Assurance Policy
category=1
document_type=pdf
related_module=institutional_policy
visibility_level=all_authenticated
description=Official policy document
effective_date=2026-07-01
review_date=2027-07-01
file=<PDF file>
change_summary=Initial upload
```

### Link Document Create

```json
{
  "title": "QA Orientation Slides",
  "category": 3,
  "document_type": "link",
  "related_module": "qa_committee",
  "visibility_level": "qa_focal_persons",
  "description": "Orientation debriefing slides for QA Focal Persons",
  "external_url": "https://example.com/slides",
  "change_summary": "Initial link upload"
}
```

Validation:

- `file` is required unless `document_type=link`.
- `external_url` is required when `document_type=link`.
- `review_date` cannot be before `effective_date`.
- `expiry_date` cannot be before `effective_date`.
- File extension must match document type when restricted.

### Document Workflow

```text
draft -> pending_review -> approved -> published
draft -> pending_review -> rejected
published -> draft when new version is uploaded
any active document -> archived
```

Approve request:

```json
{
  "comment": "Approved for publication."
}
```

Reject request:

```json
{
  "comment": "Please update the review date."
}
```

New version multipart fields:

```text
version_number=1.1
file=<updated PDF>
change_summary=Updated policy section
submit_for_review=false
```

### Document Filters

```text
search
category
document_type
related_module
visibility_level
status
is_latest
uploaded_by
approved_by
effective_date_from
effective_date_to
review_date_from
review_date_to
created_at_from
created_at_to
```

Example:

```http
GET /api/institutional-documents/documents/?status=published&search=policy
```

## 14. Pagination

Implemented custom pagination envelopes:

- accreditation list endpoints
- institutional document list endpoints

Parameters:

```text
page
page_size
```

Maximum page size:

```text
100
```

Plain DRF modules currently do not define custom pagination in this project.

## 15. Error Handling Reference

| Status | Cause | Frontend Handling |
|---:|---|---|
| 200 | Successful read/update/action | Update UI state |
| 201 | Successful create | Add record to list or redirect to detail |
| 204 | DRF hard delete may return no body in plain modules | Remove record from UI |
| 400 | Validation error or invalid payload | Show field errors |
| 401 | Missing/invalid JWT | Redirect to login |
| 403 | Authenticated but not permitted | Show access denied |
| 404 | Record not found or hidden by permissions | Show not found |
| 500 | Unexpected server error | Show generic error and log details |

Wrapped module validation example:

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "metric": ["Metric does not belong to selected component."]
  }
}
```

Plain DRF validation example:

```json
{
  "code": ["course with this code already exists."]
}
```

## 16. Rate Limits

No rate limiting is implemented in the current project.

Frontend retry recommendation:

- Do not auto-retry validation errors.
- Retry network failures only after user confirmation or a short debounce.
- Avoid retrying file uploads automatically unless the user confirms.

## 17. Complete Frontend Workflows

### Login Flow

```text
User enters username/password
Frontend validates required fields
POST /api/auth/login/
Backend authenticates user
Frontend stores access token
Frontend loads dashboard or selected module
```

### Course Monitoring Flow

```text
Load faculties/departments
Load courses
User fills lecture monitoring form
POST /api/courses/lecture-sessions/
Backend validates lecture held/reason rules
Frontend shows success or validation errors
```

### Exam Quality Flow

```text
Create/select exam session
User fills quality report
POST /api/examinations/quality-reports/
Backend validates rating fields and misconduct details
Frontend displays submitted report
```

### Lecturer Assessment Flow

```text
Load lecturer profile
Load course
Student submits 17 ratings
POST /api/lecturers/assessment-reports/
Backend calculates average_rating
Frontend displays confirmation
Admin can view lecturer assessment summary
```

### Accreditation Flow

```text
Create accreditation cycle
Load components and metrics
Submit metric values in bulk
Upload evidence
Verify evidence
Calculate component scores
Calculate PARI
Review risk classification
Handle alerts
Track corrective actions
Show analytics dashboard
```

### QA Committee Flow

```text
Create committee
Add chairperson, secretary, and members
Schedule meeting
Mark meeting as held and record attendance
Start audit cycle
Create findings from manual review or referenced module records
Create recommendations
Create action plans
Upload or link evidence
Verify evidence
Submit committee report
View QACEI and committee dashboard metrics
```

### Institutional Documents Flow

```text
Load categories
Upload file or create link document
Submit document for review
Reviewer approves or rejects
Publisher publishes
Users preview/download
Access log is created
New versions can be uploaded later
```

## 18. Testing Examples

### cURL Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_admin\",\"password\":\"StrongPass123!\"}"
```

### cURL Authenticated Request

```bash
curl http://127.0.0.1:8000/api/core/faculties/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### JavaScript Fetch

```javascript
const response = await fetch("http://127.0.0.1:8000/api/accreditation/components/", {
  headers: {
    Authorization: `Bearer ${accessToken}`,
    Accept: "application/json"
  }
});

const data = await response.json();
```

### Axios

```javascript
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    Authorization: `Bearer ${accessToken}`
  }
});

const { data } = await api.get("/api/analytics/accreditation/overview/");
```

### Multipart Upload With Fetch

```javascript
const formData = new FormData();
formData.append("title", "Quality Assurance Policy");
formData.append("category", "1");
formData.append("document_type", "pdf");
formData.append("related_module", "institutional_policy");
formData.append("visibility_level", "all_authenticated");
formData.append("file", fileInput.files[0]);
formData.append("change_summary", "Initial upload");

const response = await fetch("http://127.0.0.1:8000/api/institutional-documents/documents/", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`
  },
  body: formData
});
```

Do not manually set `Content-Type` for browser multipart requests; the browser will add the boundary.

## 19. Integration Checklist

- Base URL is configured.
- Login flow stores JWT access token.
- `Authorization: Bearer <token>` is sent for protected requests.
- JSON requests include `Content-Type: application/json`.
- File uploads use `multipart/form-data`.
- Client-side validation mirrors backend required fields.
- Rating fields enforce 1 to 5.
- Negative accreditation metric values are blocked in the UI.
- Loading states are shown during API calls.
- 400 errors display field-level validation messages.
- 401 errors redirect to login.
- 403 errors show access denied.
- 404 errors show not found or unavailable.
- Paginated responses are handled for accreditation and documents.
- Search and filters are debounced.
- File downloads and previews open in a new tab or download handler.
- Document workflow buttons are shown based on status and role.
- Accreditation calculation buttons are shown only to permitted users.
- QA Committee workflow buttons are shown based on committee role and record status.
- QACEI and committee dashboard metrics are rendered from API values instead of recalculated on the frontend.
- Complaint status updates use the backend PATCH flow so notifications and timeline entries are generated automatically.
- Student notification badges/lists read from `/api/students/notifications/`.

## 20. Known Limitations

- No explicit API versioning is implemented.
- No rate limiting is implemented.
- No production or staging base URL is configured in the repository.
- Token refresh is not documented as a custom route in the current route map; use login again if access expires unless the frontend separately integrates supported package behavior.
- Core, courses, examinations, and lecturers use plain DRF response shapes, while accreditation, analytics, and documents use wrapped responses.
- Plain DRF modules do not currently use the custom pagination envelope.
- Media storage is local filesystem storage by default.
- Public file serving configuration for production is not included in this repository.
- `DEBUG=True` in local settings means unhandled server errors can render Django debug HTML during development.

## 21. Demo Data For Local Testing

To seed or refresh realistic local dashboard data, run:

```text
python manage.py seed_dashboard_demo_data
```

The command is idempotent and creates or updates demo records across core, students, courses, lecturers, examinations, institutional documents, accreditation, QA Committee, and dashboards. It avoids file uploads and uses links for evidence where possible.

Demo users created by the command:

```text
demo_admin / StrongPass123!                 admin
demo_principal / StrongPass123!             principle_officer
demo_focal / StrongPass123!                 focal_person
demo_student / StrongPass123!               student
demo_committee_secretary / StrongPass123!   committee_secretary
demo_department_admin / StrongPass123!      department_admin
demo_readonly / StrongPass123!              read_only_viewer
```

Useful demo records:

```text
Faculty of Science
Computer Science
CSC 101 - Introduction to Computing
CSC 201 - Data Structures
CSC 401 - Software Quality Assurance
DEMO-LECT-001
Demo NUC Accreditation Readiness Cycle
Faculty of Science QA Committee
Demo Faculty Q1 Audit
Demo Quality Assurance Policy
student complaint with notification history
```

Use `demo_admin` for full management testing. Use `demo_student` to test student-only complaint and notification views. Use `demo_department_admin` to test department-scoped dashboard access.
