from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Department, Faculty

from .models import (
    CommitteeMeetingAttendance,
    QAActionEvidence,
    QAActionPlan,
    QAAuditCycle,
    QAAuditFinding,
    QACommittee,
    QACommitteeMember,
    QACommitteeReport,
    QARecommendation,
)
from .services import get_committee_effectiveness_score, summarize_external_module


class QACommitteeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            username="dqa_admin",
            email="dqa_admin@example.com",
            password="password",
        )
        self.member_user = get_user_model().objects.create_user(
            username="committee_member",
            email="member@example.com",
            password="password",
        )
        self.student_user = get_user_model().objects.create_user(
            username="student_user",
            email="student@example.com",
            password="password",
        )
        self.faculty = Faculty.objects.create(name="Faculty of Science")
        self.department = Department.objects.create(faculty=self.faculty, name="Computer Science")
        self.client.force_authenticate(self.admin)

    def committee_payload(self, **overrides):
        payload = {
            "name": "Faculty Science QA Committee",
            "scope_type": "faculty",
            "faculty": self.faculty.id,
            "description": "Faculty-level quality assurance committee.",
            "status": "active",
            "date_constituted": str(timezone.localdate()),
        }
        payload.update(overrides)
        return payload

    def create_committee(self):
        response = self.client.post("/api/qa-committee/committees/", self.committee_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data["id"]

    def create_member(self, committee_id, user=None, role="chairperson"):
        response = self.client.post(
            f"/api/qa-committee/committees/{committee_id}/members/",
            {
                "user": (user or self.admin).id,
                "role": role,
                "designation": "DQA Officer",
                "start_date": str(timezone.localdate()),
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data["id"]

    def create_audit_cycle(self, committee_id):
        response = self.client.post(
            "/api/qa-committee/audit-cycles/",
            {
                "committee": committee_id,
                "title": "Quarterly Review",
                "review_period_start": str(timezone.localdate() - timedelta(days=30)),
                "review_period_end": str(timezone.localdate()),
                "audit_type": "routine",
                "target_faculty": self.faculty.id,
                "target_department": self.department.id,
                "status": "draft",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data["id"]

    def test_committee_creation_and_duplicate_active_scope_protection(self):
        self.create_committee()
        duplicate = self.client.post("/api/qa-committee/committees/", self.committee_payload(name="Duplicate"), format="json")
        self.assertEqual(duplicate.status_code, 400)

    def test_committee_member_and_single_active_chairperson_rule(self):
        committee_id = self.create_committee()
        self.create_member(committee_id, self.admin, "chairperson")
        duplicate = self.client.post(
            f"/api/qa-committee/committees/{committee_id}/members/",
            {
                "user": self.member_user.id,
                "role": "chairperson",
                "start_date": str(timezone.localdate()),
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)

    def test_meeting_and_attendance_workflow(self):
        committee_id = self.create_committee()
        member_id = self.create_member(committee_id)
        meeting = self.client.post(
            "/api/qa-committee/meetings/",
            {
                "committee": committee_id,
                "title": "Review Meeting",
                "meeting_type": "regular",
                "scheduled_date": timezone.now().isoformat(),
                "venue": "DQA Boardroom",
                "agenda": "Review quality data.",
            },
            format="json",
        )
        self.assertEqual(meeting.status_code, 201, meeting.data)
        meeting_id = meeting.data["id"]
        held = self.client.post(f"/api/qa-committee/meetings/{meeting_id}/mark-held/", {}, format="json")
        self.assertEqual(held.status_code, 200, held.data)
        self.assertEqual(held.data["status"], "held")

        attendance = self.client.post(
            f"/api/qa-committee/meetings/{meeting_id}/attendance/",
            {"attendance": [{"member": member_id, "attendance_status": "present", "remarks": "Present"}]},
            format="json",
        )
        self.assertEqual(attendance.status_code, 200, attendance.data)
        self.assertEqual(CommitteeMeetingAttendance.objects.count(), 1)

    def test_audit_cycle_submit_finding_and_source_reference(self):
        committee_id = self.create_committee()
        audit_id = self.create_audit_cycle(committee_id)
        submitted = self.client.post(f"/api/qa-committee/audit-cycles/{audit_id}/submit/", {}, format="json")
        self.assertEqual(submitted.status_code, 200, submitted.data)
        self.assertEqual(submitted.data["status"], "submitted")

        manual = self.client.post(
            "/api/qa-committee/findings/",
            {
                "audit_cycle": audit_id,
                "source_module": "manual",
                "title": "Manual finding",
                "description": "Manual review found a gap.",
                "category": "governance",
                "severity": "medium",
                "risk_level": "moderate",
            },
            format="json",
        )
        self.assertEqual(manual.status_code, 201, manual.data)
        self.assertTrue(manual.data["finding_code"].startswith("QAF-"))

        referenced = self.client.post(
            "/api/qa-committee/findings/",
            {
                "audit_cycle": audit_id,
                "source_module": "examinations",
                "source_record_type": "ExamQualityReport",
                "source_record_id": "12",
                "title": "Referenced finding",
                "description": "Finding references examination data.",
                "category": "examination",
                "severity": "critical",
                "risk_level": "high",
            },
            format="json",
        )
        self.assertEqual(referenced.status_code, 201, referenced.data)
        self.assertEqual(referenced.data["source_record_id"], "12")

    def test_recommendation_action_plan_evidence_and_verification(self):
        committee_id = self.create_committee()
        audit_id = self.create_audit_cycle(committee_id)
        finding = self.client.post(
            "/api/qa-committee/findings/",
            {
                "audit_cycle": audit_id,
                "source_module": "manual",
                "title": "Staffing finding",
                "description": "Staffing needs attention.",
                "category": "staffing",
                "severity": "high",
                "risk_level": "high",
            },
            format="json",
        )
        finding_id = finding.data["id"]
        recommendation = self.client.post(
            "/api/qa-committee/recommendations/",
            {
                "finding": finding_id,
                "audit_cycle": audit_id,
                "title": "Recruit lecturers",
                "recommendation_text": "Recruit more academic staff.",
                "responsible_unit_type": "department",
                "responsible_faculty": self.faculty.id,
                "responsible_department": self.department.id,
                "assigned_to": self.member_user.id,
                "priority": "high",
                "due_date": str(timezone.localdate() + timedelta(days=30)),
            },
            format="json",
        )
        self.assertEqual(recommendation.status_code, 201, recommendation.data)
        recommendation_id = recommendation.data["id"]

        action = self.client.post(
            "/api/qa-committee/action-plans/",
            {
                "recommendation": recommendation_id,
                "action_description": "Advertise and shortlist candidates.",
                "owner": self.member_user.id,
                "expected_completion_date": str(timezone.localdate() + timedelta(days=20)),
                "progress_percentage": 40,
                "status": "in_progress",
            },
            format="json",
        )
        self.assertEqual(action.status_code, 201, action.data)
        action_id = action.data["id"]

        evidence = self.client.post(
            "/api/qa-committee/evidence/",
            {
                "action_plan": action_id,
                "title": "Advert evidence",
                "external_url": "https://example.com/evidence",
            },
            format="json",
        )
        self.assertEqual(evidence.status_code, 201, evidence.data)
        evidence_id = evidence.data["id"]
        verified = self.client.post(
            f"/api/qa-committee/evidence/{evidence_id}/verify/",
            {"verification_comment": "Accepted."},
            format="json",
        )
        self.assertEqual(verified.status_code, 200, verified.data)
        self.assertEqual(verified.data["verification_status"], "accepted")

    def test_action_plan_submit_evidence_file_or_link_required(self):
        committee_id = self.create_committee()
        audit_id = self.create_audit_cycle(committee_id)
        recommendation = QARecommendation.objects.create(
            audit_cycle_id=audit_id,
            title="Improve facilities",
            recommendation_text="Fix facilities.",
            responsible_unit_type="department",
            responsible_faculty=self.faculty,
            responsible_department=self.department,
            due_date=timezone.localdate() + timedelta(days=10),
            created_by=self.admin,
        )
        action = QAActionPlan.objects.create(
            recommendation=recommendation,
            action_description="Fix classrooms.",
            expected_completion_date=timezone.localdate() + timedelta(days=5),
        )
        bad_evidence = self.client.post(
            f"/api/qa-committee/action-plans/{action.id}/submit-evidence/",
            {"title": "No file or link"},
            format="json",
        )
        self.assertEqual(bad_evidence.status_code, 400)

        good_evidence = self.client.post(
            f"/api/qa-committee/action-plans/{action.id}/submit-evidence/",
            {"title": "Uploaded file", "file": SimpleUploadedFile("evidence.txt", b"done")},
            format="multipart",
        )
        self.assertEqual(good_evidence.status_code, 201, good_evidence.data)

    def test_report_submit_and_qacei_calculation(self):
        committee_id = self.create_committee()
        self.create_member(committee_id)
        meeting = self.client.post(
            "/api/qa-committee/meetings/",
            {
                "committee": committee_id,
                "title": "Held Meeting",
                "scheduled_date": timezone.now().isoformat(),
                "status": "held",
                "held_date": timezone.now().isoformat(),
            },
            format="json",
        )
        self.assertEqual(meeting.status_code, 201, meeting.data)
        audit_id = self.create_audit_cycle(committee_id)
        self.client.post(
            "/api/qa-committee/findings/",
            {
                "audit_cycle": audit_id,
                "source_module": "manual",
                "title": "Finding",
                "description": "Finding text.",
                "category": "other",
                "severity": "low",
                "risk_level": "low",
            },
            format="json",
        )
        recommendation = QARecommendation.objects.create(
            audit_cycle_id=audit_id,
            title="Recommendation",
            recommendation_text="Recommendation text.",
            responsible_unit_type="department",
            due_date=timezone.localdate() + timedelta(days=20),
        )
        QAActionPlan.objects.create(
            recommendation=recommendation,
            action_description="Action",
            expected_completion_date=timezone.localdate() + timedelta(days=10),
        )
        report = self.client.post(
            "/api/qa-committee/reports/",
            {
                "committee": committee_id,
                "audit_cycle": audit_id,
                "report_type": "quarterly",
                "reporting_period_start": str(timezone.localdate() - timedelta(days=30)),
                "reporting_period_end": str(timezone.localdate()),
                "summary": "Quarterly summary.",
            },
            format="json",
        )
        self.assertEqual(report.status_code, 201, report.data)
        submitted = self.client.post(f"/api/qa-committee/reports/{report.data['id']}/submit/", {}, format="json")
        self.assertEqual(submitted.status_code, 200, submitted.data)
        self.assertEqual(submitted.data["status"], "submitted")
        self.assertEqual(float(submitted.data["qacei_score"]), 5.0)
        self.assertEqual(get_committee_effectiveness_score(QACommittee.objects.get(pk=committee_id)), 5.0)

    def test_permission_restrictions(self):
        committee_id = self.create_committee()
        self.client.force_authenticate(self.student_user)
        response = self.client.get("/api/qa-committee/committees/")
        self.assertEqual(response.status_code, 403)
        forbidden = self.client.post("/api/qa-committee/committees/", self.committee_payload(name="Forbidden"), format="json")
        self.assertEqual(forbidden.status_code, 403)

    def test_role_permission_edges_for_committee_endpoints(self):
        self.create_committee()
        role_expectations = {
            "admin": (200, 201),
            "super_admin": (200, 201),
            "dqa_admin": (200, 201),
            "principle_officer": (200, 201),
            "committee_chairperson": (200, 201),
            "committee_secretary": (200, 201),
            "qa_focal_person": (200, 201),
            "focal_person": (200, 201),
            "committee_member": (200, 403),
            "department_admin": (200, 403),
            "faculty_admin": (200, 403),
            "read_only_viewer": (200, 403),
            "student": (403, 403),
            "unknown_role": (403, 403),
        }

        for role, (expected_get, expected_post) in role_expectations.items():
            user = get_user_model().objects.create_user(username=f"{role}_qa_user", password="password")
            user.profile.status = role
            user.profile.save()
            self.client.force_authenticate(user)

            with self.subTest(role=role, method="GET"):
                response = self.client.get("/api/qa-committee/committees/")
                self.assertEqual(response.status_code, expected_get, response.data)

            with self.subTest(role=role, method="POST"):
                response = self.client.post(
                    "/api/qa-committee/committees/",
                    self.committee_payload(name=f"{role} Committee", status="inactive"),
                    format="json",
                )
                self.assertEqual(response.status_code, expected_post, response.data)

    def test_summary_and_missing_module_service(self):
        self.create_committee()
        summary = self.client.get("/api/qa-committee/summary/")
        self.assertEqual(summary.status_code, 200, summary.data)
        self.assertIn("total_committees", summary.data)

        with patch("qa_committee.services.safe_model_import", return_value=None):
            data = summarize_external_module("lectures")
        self.assertEqual(data["status"], "module_not_available")
