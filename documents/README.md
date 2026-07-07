# Institutional Documents API

API-backed repository for section 4.4 of the DQA Digital Quality Assurance Platform: institutional policy, strategy, orientation materials, SOPs, manuals, templates, governance documents, security guidelines, accreditation templates, and official DQA references.

Base URL:

```text
/api/institutional-documents/
```

## Authentication And Roles

Use the existing JWT login endpoint:

```http
POST /api/auth/login/
```

Then pass:

```http
Authorization: Bearer <access_token>
```

Role behavior:

- DQA Admin: full upload, update, archive, review, publish, and logs access.
- Director DQA / principle officer: review and publish.
- QA Focal Person: upload and view permitted documents.
- HOD/Dean and committee-style access: view documents for their visibility level.
- General authenticated user: view `all_authenticated` and `public` published documents.
- Anonymous user: view/download only `public` published documents.

## Response Shape

Success:

```json
{
  "success": true,
  "message": "Document uploaded successfully.",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "file": ["File is required unless document type is link."]
  }
}
```

Paginated lists include:

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

## Status Flow

```text
draft -> pending_review -> approved -> published
draft -> pending_review -> rejected
published -> draft when a new version is uploaded
any active document -> archived
```

Rules:

- A document cannot be submitted for review without a file or link.
- A document cannot be approved without at least one version.
- A document cannot be published unless it is approved.
- Uploading a new version does not overwrite old files.
- Preview and download create access-log records.

## Endpoints

Categories:

```text
GET    /categories/
POST   /categories/
GET    /categories/{id}/
PATCH  /categories/{id}/
DELETE /categories/{id}/
```

Documents:

```text
GET    /documents/
POST   /documents/
GET    /documents/{id}/
PATCH  /documents/{id}/
DELETE /documents/{id}/
```

Workflow:

```text
POST /documents/{id}/submit-for-review/
POST /documents/{id}/approve/
POST /documents/{id}/reject/
POST /documents/{id}/publish/
POST /documents/{id}/archive/
POST /documents/{id}/new-version/
```

File access:

```text
GET /documents/{id}/preview/
GET /documents/{id}/download/
```

Versions and logs:

```text
GET /documents/{id}/versions/
GET /versions/{version_id}/
GET /access-logs/
```

## Create Document With File

Use `multipart/form-data`.

```text
POST /api/institutional-documents/documents/
```

Fields:

```text
title=Quality Assurance Policy & Strategy
category=1
document_type=pdf
related_module=institutional_policy
visibility_level=all_authenticated
description=Official University of Ibadan Quality Assurance Policy document
effective_date=2026-07-01
review_date=2027-07-01
file=<PDF file>
change_summary=Initial upload
```

## Create Document As Link

```http
POST /api/institutional-documents/documents/
Content-Type: application/json
```

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

## Submit For Review

```http
POST /api/institutional-documents/documents/5/submit-for-review/
```

```json
{
  "success": true,
  "message": "Document submitted for review.",
  "data": {
    "id": 5,
    "status": "pending_review"
  }
}
```

## Approve

```http
POST /api/institutional-documents/documents/5/approve/
Content-Type: application/json
```

```json
{
  "comment": "Document approved for publication."
}
```

## Reject

```http
POST /api/institutional-documents/documents/5/reject/
Content-Type: application/json
```

```json
{
  "comment": "Please update the review date and replace the incorrect file."
}
```

## Publish

```http
POST /api/institutional-documents/documents/5/publish/
```

Publishing succeeds only when the current status is `approved`.

## Upload New Version

Use `multipart/form-data`.

```text
POST /api/institutional-documents/documents/5/new-version/
```

Fields:

```text
file=<updated PDF>
version_number=1.1
change_summary=Updated policy section and review timeline
submit_for_review=false
```

For link documents, send `external_url` instead of `file`.

## Download And Preview

```http
GET /api/institutional-documents/documents/5/download/
GET /api/institutional-documents/documents/5/preview/
```

Both endpoints log:

- document
- version
- user
- action
- IP address
- user agent
- timestamp

## Filtering Examples

```http
GET /api/institutional-documents/documents/?category=1&status=published&search=policy
GET /api/institutional-documents/documents/?document_type=pdf&related_module=institutional_policy
GET /api/institutional-documents/documents/?visibility_level=all_authenticated
GET /api/institutional-documents/documents/?effective_date_from=2026-07-01&effective_date_to=2026-12-31
GET /api/institutional-documents/documents/?review_date_from=2027-01-01
GET /api/institutional-documents/documents/?uploaded_by=2&approved_by=1
```

Search checks title, description, and tag names.

## Validation Rules

- `title` is required.
- `category` is required.
- `document_type` is required.
- `visibility_level` is required.
- `related_module` is required.
- `file` is required unless `document_type` is `link`.
- `external_url` is required when `document_type` is `link`.
- `review_date` must not be before `effective_date`.
- `expiry_date` must not be before `effective_date`.
- `version_number` must be unique per document.
- File extensions must match document type:
  - `pdf`: `.pdf`
  - `word`: `.doc`, `.docx`, `.odt`
  - `powerpoint`: `.ppt`, `.pptx`
  - `spreadsheet`: `.xls`, `.xlsx`, `.csv`
  - `image`: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`

## Frontend Notes

- Call `GET /categories/` first; default categories are created automatically if missing.
- Use `multipart/form-data` for file documents and JSON for link documents.
- Do not assume a newly uploaded document is visible to normal users; publish it first.
- After `new-version`, the document returns to `draft` unless `submit_for_review=true`.
- Use `/versions/` to display document history.
- Use `/access-logs/` only for audit/admin screens.
