# UI-AReQuM Accreditation API

Backend-only API for the University of Ibadan Accreditation Readiness and Quality Monitoring Framework.

## Authentication

Base URL: `/api`

All accreditation and accreditation analytics endpoints require authentication. Send the JWT access token already issued by the auth API:

```http
Authorization: Bearer <access_token>
```

Minimal role behavior:

- Superuser, staff, `admin`, and `principle_officer`: full access.
- `focal_person`: submit data, upload evidence, and update corrective-action progress.
- Other authenticated users: read access.
- Anonymous users: denied.

Success response shape:

```json
{
  "success": true,
  "message": "Request completed successfully.",
  "data": {}
}
```

Error response shape:

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "metric": ["Metric does not belong to selected component."]
  }
}
```

Paginated list response shape:

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

## Endpoint List

- `GET|POST /api/accreditation/cycles/`
- `GET|PATCH /api/accreditation/cycles/{id}/`
- `PATCH /api/accreditation/cycles/{id}/close/`
- `GET|POST /api/accreditation/components/`
- `GET|POST /api/accreditation/metrics/`
- `GET|POST /api/accreditation/submissions/`
- `POST /api/accreditation/submissions/bulk/`
- `GET|POST /api/accreditation/evidence/`
- `GET|PATCH /api/accreditation/evidence/{id}/`
- `PATCH /api/accreditation/evidence/{id}/verify/`
- `PATCH /api/accreditation/evidence/{id}/reject/`
- `POST /api/accreditation/cycles/{cycle_id}/programmes/{programme_id}/calculate-component-scores/`
- `POST /api/accreditation/cycles/{cycle_id}/programmes/{programme_id}/calculate-pari/`
- `GET|POST /api/accreditation/alerts/`
- `PATCH /api/accreditation/alerts/{id}/acknowledge/`
- `PATCH /api/accreditation/alerts/{id}/resolve/`
- `PATCH /api/accreditation/alerts/{id}/escalate/`
- `GET|POST /api/accreditation/actions/`
- `PATCH /api/accreditation/actions/{id}/progress/`
- `PATCH /api/accreditation/actions/{id}/submit/`
- `PATCH /api/accreditation/actions/{id}/verify/`
- `PATCH /api/accreditation/actions/{id}/reject/`
- `PATCH /api/accreditation/actions/{id}/close/`
- `GET /api/analytics/accreditation/overview/`
- `GET /api/analytics/accreditation/programmes-by-risk/`
- `GET /api/analytics/accreditation/component-performance/`
- `GET /api/analytics/accreditation/early-warning/`
- `GET /api/analytics/accreditation/faculty-summary/`
- `GET /api/analytics/accreditation/department-summary/`
- `GET /api/analytics/accreditation/timeline/`

Useful filters on list endpoints: `cycle`, `programme`, `faculty`, `department`, `component`, `status`, `risk_classification`, `reporting_period`, `date_from`, `date_to`.

## A. Create Accreditation Cycle

```http
POST /api/accreditation/cycles/
Content-Type: application/json
```

```json
{
  "title": "2026 NUC Readiness",
  "academic_session": "2026/2027",
  "semester": "First",
  "accreditation_body": "NUC",
  "accreditation_type": "Full",
  "faculty": "Science",
  "department": "Computer Science",
  "programme": "4",
  "start_date": "2026-07-01",
  "submission_deadline": "2026-08-15",
  "internal_review_deadline": "2026-08-30",
  "external_visit_date": "2026-10-10",
  "status": "submission_open"
}
```

## B. Submit Curriculum Delivery Form

```http
POST /api/accreditation/submissions/bulk/
Content-Type: application/json
```

```json
{
  "cycle": 1,
  "programme": "4",
  "component": "curriculum_delivery",
  "source_unit": "Department of Computer Science",
  "reporting_period": "2026-Q3",
  "responses": [
    { "metric": "lectures_scheduled", "numeric_value": 40 },
    { "metric": "lectures_held", "numeric_value": 34 },
    { "metric": "topics_planned", "numeric_value": 20 },
    { "metric": "topics_completed", "numeric_value": 16 }
  ]
}
```

Duplicate submissions for the same cycle, programme, component, metric, and reporting period are updated consistently.

## C. Upload Evidence

Use `multipart/form-data`.

```http
POST /api/accreditation/evidence/
```

```text
cycle=1
programme=4
component=2
metric=18
title=Approved course outline
evidence_type=course_outline
file=<binary file>
```

## D. Verify Evidence

```http
PATCH /api/accreditation/evidence/12/verify/
Content-Type: application/json
```

```json
{
  "reviewer_comment": "Evidence is complete and legible."
}
```

Reject evidence:

```json
{
  "reviewer_comment": "Please upload a signed copy.",
  "rejection_reason": "Unsigned document"
}
```

## E. Calculate Component Score

```http
POST /api/accreditation/cycles/1/programmes/4/calculate-component-scores/
```

```json
{
  "success": true,
  "message": "Component scores calculated.",
  "data": {
    "programme": "4",
    "cycle": 1,
    "scores": [
      {
        "component": "curriculum_delivery",
        "score": 82.5,
        "status": "good",
        "metrics": {
          "lecture_delivery_rate": 85,
          "course_coverage": 80
        }
      }
    ]
  }
}
```

Formula behavior: missing values and division by zero return `null` internally and are skipped from component-score averages.

## F. Calculate PARI

```http
POST /api/accreditation/cycles/1/programmes/4/calculate-pari/
```

```json
{
  "success": true,
  "message": "PARI calculated.",
  "data": {
    "programme": "4",
    "cycle": 1,
    "pari_score": 74.2,
    "classification": "moderate_risk",
    "breakdown": [
      {
        "component": "staffing",
        "weight": 25,
        "score": 70,
        "weighted_score": 17.5
      }
    ],
    "alerts_created": 1
  }
}
```

PARI classification:

- `80-100`: `accreditation_ready`
- `60-79`: `moderate_risk`
- Below `60`: `high_risk`

## G. Fetch Overview Dashboard

```http
GET /api/analytics/accreditation/overview/?faculty=Science
```

```json
{
  "total_programmes_monitored": 12,
  "accreditation_ready_count": 7,
  "moderate_risk_count": 4,
  "high_risk_count": 1,
  "average_pari_score": 78.4,
  "open_alerts": 6,
  "overdue_actions": 2,
  "evidence_completion_rate": 71.43,
  "timely_submission_rate": 88.9
}
```

## H. Fetch Programmes By Risk

```http
GET /api/analytics/accreditation/programmes-by-risk/
```

```json
{
  "accreditation_ready": [{ "programme": "4", "pari_score": 84.5 }],
  "moderate_risk": [{ "programme": "9", "pari_score": 72.0 }],
  "high_risk": [{ "programme": "14", "pari_score": 52.25 }]
}
```

## I. Create Corrective Action

```http
POST /api/accreditation/actions/
Content-Type: application/json
```

```json
{
  "cycle": 1,
  "programme": "4",
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

## J. Update Corrective Action Progress

```http
PATCH /api/accreditation/actions/9/progress/
Content-Type: application/json
```

```json
{
  "progress_percentage": 60,
  "reviewer_comment": "Recruitment memo submitted to the faculty."
}
```

Submit, verify, reject, or close:

```http
PATCH /api/accreditation/actions/9/submit/
PATCH /api/accreditation/actions/9/verify/
PATCH /api/accreditation/actions/9/reject/
PATCH /api/accreditation/actions/9/close/
```
