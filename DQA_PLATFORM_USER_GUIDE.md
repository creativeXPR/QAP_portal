# DQA Digital Quality Assurance Platform User Guide

This guide explains the parts of the DQA Digital Quality Assurance Platform implemented in this project. It is written for non-technical users, frontend developers, QA officers, administrators, and stakeholders who need to understand how the system works.

## 1. What This System Does

The system supports three major areas of DQA work:

1. UI-AReQuM Accreditation Readiness
2. Accreditation Analytics and Dashboard Reporting
3. Institutional Documents Repository

Together, these modules help the Directorate of Quality Assurance collect accreditation data, monitor programme readiness, calculate risk, trigger early warnings, manage corrective actions, and store official DQA documents.

## 2. Important Acronyms And Terms

**DQA**  
Directorate of Quality Assurance.

**QA**  
Quality Assurance. This means the process of checking, improving, and documenting the quality of academic and administrative work.

**UI-AReQuM**  
University of Ibadan Accreditation Readiness and Quality Monitoring Framework. This is the accreditation readiness system used to continuously monitor programmes before accreditation visits.

**PARI**  
Programme Accreditation Readiness Index. This is a score from 0 to 100 that shows how ready a programme is for accreditation.

**QACEI**  
QA Committee Effectiveness Index. This measures how active and effective a QA committee is.

**Cycle**  
An accreditation monitoring period. For example, "2026 NUC Readiness" may be one cycle.

**Component**  
A major area being monitored, such as staffing, curriculum delivery, infrastructure, research, or QA committee performance.

**Metric**  
A specific data point under a component. For example, under curriculum delivery, metrics include lectures scheduled, lectures held, topics planned, and topics completed.

**Evidence**  
A file or document uploaded to support submitted data. Examples include course outlines, laboratory photos, attendance records, reports, and approved templates.

**Early Warning Alert**  
A warning created by the system when a programme appears to be at risk.

**Corrective Action**  
An action assigned to fix a problem, such as recruiting more staff, improving facilities, uploading missing documents, or resolving poor performance indicators.

## 3. User Roles

The system uses roles to decide what each user can do.

**Admin / DQA Admin**  
Can create and manage most records, approve documents, publish documents, calculate scores, and manage alerts and corrective actions.

**Principle Officer / Director-Level User**  
Can perform high-level review, approval, and publishing actions.

**QA Focal Person**  
Can submit accreditation data, upload evidence, and support validation of unit-level information.

**Department or Unit User**  
Can submit data for their unit where permitted.

**General Authenticated User**  
Can view allowed dashboards and published documents.

**Anonymous User**  
Can only access public documents, if public access is allowed.

## 4. UI-AReQuM Accreditation Module

The accreditation module helps DQA monitor whether academic programmes are ready for accreditation.

### 4.1 Main Workflow

The normal workflow is:

1. DQA creates an accreditation cycle.
2. Components and metrics are selected or loaded.
3. Departments or QA focal persons submit data.
4. Evidence files are uploaded.
5. DQA reviews or verifies the evidence.
6. The system calculates component scores.
7. The system calculates PARI.
8. The programme receives a risk classification.
9. Early warning alerts are created if needed.
10. Corrective actions are created and tracked.
11. Dashboards show progress and risk.

### 4.2 Accreditation Components

The system supports these monitoring areas:

1. Academic Staffing Monitoring
2. Curriculum Delivery Monitoring
3. Student Learning Experience Monitoring
4. Examination Quality Monitoring
5. Laboratory and Practical Facilities Monitoring
6. Library and Learning Resources Monitoring
7. Infrastructure Monitoring
8. Research and Innovation Monitoring
9. Student Support Services Monitoring
10. QA Committee Performance Monitoring
11. Programme Accreditation Readiness Index, PARI

### 4.3 Examples Of Data Collected

For staffing:

- Total students
- Total academic staff
- Staff with PhD
- Staff meeting NUC requirement
- Required staff

For curriculum delivery:

- Lectures scheduled
- Lectures held
- Topics planned
- Topics completed
- CCMAS-aligned courses
- Total courses

For examination quality:

- Malpractice cases
- Number of candidates
- Exam date
- Result release date

For QA committee performance:

- Total QA score
- Maximum possible QA score

## 5. PARI: Programme Accreditation Readiness Index

PARI is the main readiness score.

It combines important component scores into one final score from 0 to 100.

### 5.1 PARI Weighting

The score is based on these weights:

| Component | Weight |
|---|---:|
| Staffing | 25% |
| Curriculum Delivery | 20% |
| Infrastructure | 15% |
| Library Resources | 10% |
| Research | 10% |
| Student Outcomes | 10% |
| QA Compliance | 10% |

### 5.2 PARI Classification

| PARI Score | Meaning |
|---:|---|
| 80 to 100 | Accreditation Ready |
| 60 to 79 | Moderate Risk |
| Below 60 | High Risk |

If the score is below 80, the system can create an early warning alert.

## 6. Early Warning System

The early warning system helps DQA identify problems early instead of waiting until accreditation season.

Alerts can be triggered by:

- PARI below 80
- Staffing shortage
- Low lecture delivery
- Poor infrastructure
- Weak research output
- Student dissatisfaction
- Laboratory functionality below benchmark
- Library resource gaps
- Poor QA committee performance
- Delayed result release
- High complaint rate

Each alert has:

- Programme
- Cycle
- Component
- Trigger type
- Severity
- Message
- Status

Alert statuses include:

- Open
- Acknowledged
- In progress
- Resolved
- Escalated

## 7. Corrective Actions

Corrective actions are used to track how identified problems are fixed.

Example:

A programme has low staffing compliance. DQA creates a corrective action called "Recruit adjunct lecturers". The department updates progress until the action is submitted, verified, and closed.

Corrective action statuses include:

- Open
- Assigned
- In progress
- Submitted for validation
- Validated
- Verified
- Rejected
- Overdue
- Escalated
- Closed

## 8. Accreditation Analytics And Dashboards

The analytics module summarizes accreditation data for dashboard screens.

It supports:

- University accreditation overview
- Programmes grouped by risk
- Component performance
- Early warning summary
- Faculty summary
- Department summary
- Timeline of PARI, alerts, and evidence

### 8.1 Dashboard Questions The System Can Answer

- How many programmes are being monitored?
- How many programmes are accreditation ready?
- How many are moderate risk?
- How many are high risk?
- What is the average PARI score?
- Which components are weakest?
- Which faculty has the most alerts?
- Which departments have overdue actions?
- How complete is the evidence submission?

## 9. Institutional Documents Module

The institutional documents module is a digital repository for official DQA documents.

It manages:

- Quality Assurance Policy and Strategy
- Orientation Debriefing Slides
- SOPs
- User manuals
- Reporting templates
- Data governance guidelines
- Security guidelines
- Accreditation templates
- Other DQA reference documents

## 10. Institutional Document Workflow

The normal document workflow is:

1. Admin uploads a document or adds a document link.
2. Document metadata is added.
3. The document is categorized.
4. The document is submitted for review.
5. A reviewer approves or rejects it.
6. Approved documents are published.
7. Authorized users can view or download published documents.
8. The system logs every preview or download.
9. Updated versions can be uploaded.
10. Old versions remain preserved.
11. Documents can be archived when no longer active.

## 11. Document Categories

The system supports these default categories:

- Policy Documents
- Strategy Documents
- Orientation Materials
- Accreditation Documents
- Standard Operating Procedures
- User Manuals
- Reporting Templates
- Data Governance Documents
- Security Guidelines
- General Reference Documents

## 12. Document Statuses

| Status | Meaning |
|---|---|
| Draft | Uploaded but not yet submitted for review |
| Pending Review | Waiting for reviewer decision |
| Approved | Approved but not yet published |
| Published | Available to permitted users |
| Rejected | Returned or rejected by reviewer |
| Archived | Retired from normal use |
| Expired | No longer valid after expiry date |

## 13. Document Visibility Levels

Documents can be restricted to different audiences:

- Private
- DQA only
- QA focal persons
- HODs and Deans
- Committee members
- All authenticated users
- Public

This helps DQA control who sees sensitive internal documents.

## 14. What The Frontend Should Show

Frontend screens can be organized around these user tasks.

### 14.1 Accreditation Screens

Suggested screens:

- Accreditation cycle list
- Create or edit cycle
- Component and metric setup
- Bulk data submission form
- Evidence upload page
- Component score page
- PARI result page
- Risk classification dashboard
- Early warning alerts page
- Corrective actions tracker

### 14.2 Analytics Screens

Suggested dashboard widgets:

- Total programmes monitored
- Accreditation-ready count
- Moderate-risk count
- High-risk count
- Average PARI score
- Open alerts
- Overdue corrective actions
- Evidence completion rate
- Component performance chart
- Programmes by risk chart
- Faculty and department summaries

### 14.3 Documents Screens

Suggested screens:

- Document library
- Category management
- Upload document
- Add document link
- Document details
- Submit for review
- Approve or reject document
- Publish document
- Version history
- Access logs

## 15. Data Flow For Frontend Developers

### 15.1 Accreditation Data Flow

1. User logs in and receives a JWT token.
2. Frontend loads accreditation components.
3. Frontend creates or selects a cycle.
4. User submits metric values.
5. User uploads evidence if needed.
6. Reviewer verifies evidence.
7. Frontend calls component score calculation.
8. Frontend calls PARI calculation.
9. Frontend displays PARI score and risk classification.
10. Frontend displays alerts and corrective actions.

### 15.2 Documents Data Flow

1. User logs in.
2. Frontend loads document categories.
3. User uploads a file or link.
4. User submits the document for review.
5. Reviewer approves or rejects.
6. Publisher publishes approved document.
7. Users preview or download the document.
8. System records access logs.
9. New versions can be uploaded later.

## 16. Main API Areas

Developer API details are documented in:

- `accreditation/README.md`
- `documents/README.md`

High-level endpoint groups:

```text
/api/auth/
/api/accreditation/
/api/analytics/accreditation/
/api/institutional-documents/
```

## 17. Example Non-Technical Walkthrough

Imagine the Department of Computer Science is preparing for NUC accreditation.

1. DQA creates a 2026 accreditation cycle.
2. The department submits staffing, curriculum, infrastructure, research, library, and QA committee data.
3. The department uploads evidence such as course outlines, staffing records, and reports.
4. The system calculates component scores.
5. The system calculates PARI.
6. If PARI is 82, the programme is accreditation ready.
7. If PARI is 72, the programme is moderate risk.
8. If PARI is 55, the programme is high risk.
9. The system creates alerts for weak areas.
10. DQA creates corrective actions.
11. The department updates progress until the actions are verified.
12. Dashboards show DQA which programmes need urgent attention.

At the same time, DQA can upload policy documents, templates, SOPs, and orientation slides into the document repository. Users can access the documents according to their roles.

## 18. What Was Implemented

The implemented work includes:

- UI-AReQuM accreditation API
- Accreditation cycle management
- Component and metric setup
- Bulk metric submission
- Evidence upload and review
- Formula calculation
- Component score calculation
- PARI calculation
- Risk classification
- Early warning alerts
- Corrective actions
- Accreditation analytics dashboard APIs
- Institutional documents repository
- Document category management
- Document upload and link support
- Document review and publishing workflow
- Document versioning
- Document preview and download logging
- Role-based access rules
- Frontend API documentation
- Automated tests for the implemented modules

## 19. Current Limitations

The current system is backend/API focused.

It does not yet include:

- A completed frontend interface
- Real institutional programme database integration
- Automated email or SMS notifications
- Advanced report export templates
- External storage integration for large production files

These can be added later without changing the core purpose of the modules.

## 20. Simple Explanation For Presentation

The platform helps DQA move from last-minute accreditation preparation to continuous accreditation readiness.

It collects data from departments, calculates readiness scores, highlights risk areas, tracks corrective actions, and stores official DQA documents in one controlled repository.

The PARI score gives management a quick view of whether each programme is ready, at moderate risk, or at high risk before accreditation visits happen.
