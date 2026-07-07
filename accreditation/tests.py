import shutil
import tempfile
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import (
    AccreditationComponent,
    AccreditationCycle,
    AccreditationMetric,
    ComponentScore,
    CorrectiveAction,
    EarlyWarningAlert,
    Evidence,
    MetricSubmission,
    PARIResult,
)
from .services import calculate_component_scores, calculate_pari, ensure_default_components_and_metrics


MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AccreditationApiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            username="dqa", email="dqa@example.com", password="password"
        )
        self.client.force_authenticate(self.user)
        ensure_default_components_and_metrics()
        self.cycle = AccreditationCycle.objects.create(
            title="2026 NUC Readiness",
            academic_session="2026/2027",
            semester="First",
            accreditation_body="NUC",
            accreditation_type="Full",
            faculty="Science",
            department="Computer Science",
            programme="4",
            start_date=date.today(),
            submission_deadline=date.today() + timedelta(days=7),
            status="submission_open",
        )

    def test_cycle_and_metric_creation(self):
        self.assertEqual(AccreditationCycle.objects.count(), 1)
        component = AccreditationComponent.objects.get(code="curriculum_delivery")
        metric = AccreditationMetric.objects.get(component=component, code="lecture_delivery_rate")
        self.assertEqual(component.weight, 20)
        self.assertTrue(metric.required_evidence)

    def test_bulk_submission_updates_duplicate_and_rejects_invalid_metric(self):
        payload = {
            "cycle": self.cycle.id,
            "programme": "4",
            "component": "curriculum_delivery",
            "reporting_period": "2026-Q3",
            "responses": [{"metric": "lectures_scheduled", "numeric_value": "40"}],
        }
        response = self.client.post("/api/accreditation/submissions/bulk/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        payload["responses"][0]["numeric_value"] = "42"
        response = self.client.post("/api/accreditation/submissions/bulk/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(MetricSubmission.objects.count(), 1)
        self.assertEqual(MetricSubmission.objects.get().numeric_value, 42)

        payload["responses"] = [{"metric": "not_a_metric", "numeric_value": "1"}]
        response = self.client.post("/api/accreditation/submissions/bulk/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])

        payload["responses"] = [{"metric": "lectures_scheduled", "numeric_value": "-1"}]
        response = self.client.post("/api/accreditation/submissions/bulk/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])

    def test_bulk_submission_requires_authentication(self):
        client = APIClient()
        response = client.post("/api/accreditation/submissions/bulk/", {}, format="json")
        self.assertIn(response.status_code, [401, 403])

    def test_normal_user_cannot_calculate_pari(self):
        normal_user = get_user_model().objects.create_user(username="student_user", password="password")
        self.client.force_authenticate(normal_user)
        response = self.client.post(f"/api/accreditation/cycles/{self.cycle.id}/programmes/4/calculate-pari/")
        self.assertEqual(response.status_code, 403)

    def test_evidence_upload_and_review_lifecycle(self):
        component = AccreditationComponent.objects.get(code="curriculum_delivery")
        upload = SimpleUploadedFile("outline.pdf", b"evidence", content_type="application/pdf")
        response = self.client.post(
            "/api/accreditation/evidence/",
            {
                "cycle": self.cycle.id,
                "programme": "4",
                "component": component.id,
                "title": "Course Outline",
                "evidence_type": "outline",
                "file": upload,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        evidence_id = response.data["data"]["id"]
        evidence = Evidence.objects.get(pk=evidence_id)
        self.assertEqual(evidence.uploaded_by, self.user)

        response = self.client.patch(f"/api/accreditation/evidence/{evidence_id}/verify/", {"reviewer_comment": "ok"}, format="json")
        self.assertEqual(response.status_code, 200)
        evidence.refresh_from_db()
        self.assertEqual(evidence.verification_status, "verified")

        response = self.client.patch(
            f"/api/accreditation/evidence/{evidence_id}/reject/",
            {"reviewer_comment": "replace", "rejection_reason": "unclear"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        evidence.refresh_from_db()
        self.assertEqual(evidence.verification_status, "rejected")

    def test_component_score_pari_alert_and_analytics_overview(self):
        payload = {
            "cycle": self.cycle.id,
            "programme": "4",
            "component": "curriculum_delivery",
            "reporting_period": "2026-Q3",
            "responses": [
                {"metric": "lectures_scheduled", "numeric_value": "40"},
                {"metric": "lectures_held", "numeric_value": "34"},
                {"metric": "topics_planned", "numeric_value": "20"},
                {"metric": "topics_completed", "numeric_value": "16"},
            ],
        }
        self.client.post("/api/accreditation/submissions/bulk/", payload, format="json")
        response = self.client.post(f"/api/accreditation/cycles/{self.cycle.id}/programmes/4/calculate-component-scores/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ComponentScore.objects.filter(cycle=self.cycle, programme="4").exists())

        response = self.client.post(f"/api/accreditation/cycles/{self.cycle.id}/programmes/4/calculate-pari/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PARIResult.objects.count(), 1)
        self.assertGreaterEqual(EarlyWarningAlert.objects.count(), 1)

        response = self.client.get("/api/analytics/accreditation/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("average_pari_score", response.data["data"])

    def test_component_score_handles_date_metrics(self):
        payload = {
            "cycle": self.cycle.id,
            "programme": "BSc Computer Science",
            "component": "examination_quality",
            "reporting_period": "2026-Q3",
            "responses": [
                {"metric": "cases", "numeric_value": "2"},
                {"metric": "candidates", "numeric_value": "395"},
                {"metric": "exam_date", "date_value": "2026-07-10"},
                {"metric": "result_release_date", "date_value": "2026-07-31"},
            ],
        }
        response = self.client.post("/api/accreditation/submissions/bulk/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)

        response = self.client.post(
            f"/api/accreditation/cycles/{self.cycle.id}/programmes/BSc%20Computer%20Science/calculate-component-scores/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        examination_score = ComponentScore.objects.get(
            cycle=self.cycle,
            programme="BSc Computer Science",
            component__code="examination_quality",
        )
        self.assertEqual(examination_score.metrics["exam_date"], "2026-07-10")
        self.assertEqual(examination_score.metrics["result_release_date"], "2026-07-31")

    def test_service_calculation_and_risk_classification_storage(self):
        component = AccreditationComponent.objects.get(code="staffing")
        for metric_code, value in {
            "total_students": 200,
            "total_academic_staff": 10,
            "staff_with_phd": 4,
            "staff_meeting_nuc_requirement": 5,
            "required_staff": 10,
        }.items():
            MetricSubmission.objects.create(
                cycle=self.cycle,
                programme="4",
                component=component,
                metric=AccreditationMetric.objects.get(component=component, code=metric_code),
                numeric_value=value,
                reporting_period="2026-Q3",
                submitted_by=self.user,
            )
        scores = calculate_component_scores(self.cycle, "4", self.user)
        self.assertTrue(any(item["component"] == "staffing" for item in scores))
        result = calculate_pari(self.cycle, "4", self.user)
        self.assertIn(result["classification"], ["moderate_risk", "high_risk", "accreditation_ready"])

    def test_alert_and_corrective_action_lifecycle_and_filters(self):
        component = AccreditationComponent.objects.get(code="staffing")
        alert = EarlyWarningAlert.objects.create(
            cycle=self.cycle,
            programme="4",
            component=component,
            trigger_type="staffing_shortage",
            severity="high",
            message="Staffing below benchmark.",
        )
        response = self.client.patch(f"/api/accreditation/alerts/{alert.id}/acknowledge/")
        self.assertEqual(response.status_code, 200)
        alert.refresh_from_db()
        self.assertEqual(alert.status, "acknowledged")

        response = self.client.post(
            "/api/accreditation/actions/",
            {
                "cycle": self.cycle.id,
                "programme": "4",
                "component": component.id,
                "alert": alert.id,
                "title": "Recruit adjunct staff",
                "description": "Close short-term staffing gap.",
                "priority": "high",
                "deadline": str(date.today() + timedelta(days=30)),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        action_id = response.data["data"]["id"]
        response = self.client.patch(
            f"/api/accreditation/actions/{action_id}/progress/",
            {"progress_percentage": 50},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(f"/api/accreditation/actions/{action_id}/submit/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(f"/api/accreditation/actions/{action_id}/verify/", {"reviewer_comment": "done"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CorrectiveAction.objects.get(pk=action_id).status, "verified")

        response = self.client.get("/api/accreditation/actions/", {"component": "staffing"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertIn("pagination", response.data)
