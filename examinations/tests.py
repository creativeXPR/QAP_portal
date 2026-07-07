from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Department, Faculty
from .models import ExamQualityReport, ExamSession


class ExaminationsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="exam_user", password="password")
        self.client.force_authenticate(self.user)
        self.faculty = Faculty.objects.create(name="Faculty of Science")
        self.department = Department.objects.create(faculty=self.faculty, name="Statistics")

    def report_payload(self, exam_session_id):
        return {
            "exam_session": exam_session_id,
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
            "observed_misconduct": False,
            "incident_description": "",
            "action_taken": "",
            "overall_rating": 4,
            "suggestions_for_improvement": "Keep current standard.",
        }

    def test_exam_session_and_quality_report_endpoints(self):
        response = self.client.post(
            "/api/examinations/exam-sessions/",
            {
                "department": self.department.id,
                "course_code_title": "STA 101 - Introductory Statistics",
                "exam_date": "2026-07-20",
                "venue": "Hall A",
                "academic_session": "First Semester 2026/2027",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        exam_session_id = response.data["id"]

        response = self.client.post(
            "/api/examinations/quality-reports/",
            self.report_payload(exam_session_id),
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(ExamQualityReport.objects.get().student, self.user)

        invalid_payload = {**self.report_payload(exam_session_id), "observed_misconduct": True, "incident_description": ""}
        response = self.client.post("/api/examinations/quality-reports/", invalid_payload, format="json")
        self.assertEqual(response.status_code, 400)

        invalid_rating = {**self.report_payload(exam_session_id), "overall_rating": 6}
        response = self.client.post("/api/examinations/quality-reports/", invalid_rating, format="json")
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/api/examinations/quality-reports/", {"observed_misconduct": False, "search": "STA"})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_examinations_require_authentication(self):
        anonymous = APIClient()
        response = anonymous.get("/api/examinations/exam-sessions/")
        self.assertIn(response.status_code, [401, 403])
