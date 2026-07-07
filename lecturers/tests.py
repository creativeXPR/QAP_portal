from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Department, Faculty
from courses.models import Course
from .models import AssessmentReport, LecturerProfile


class LecturersApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="student_user", password="password")
        self.lecturer_user = get_user_model().objects.create_user(username="lecturer_user", password="password")
        self.client.force_authenticate(self.user)
        self.faculty = Faculty.objects.create(name="Faculty of Science")
        self.department = Department.objects.create(faculty=self.faculty, name="Mathematics")
        self.course = Course.objects.create(department=self.department, code="MTH 101", title="Algebra")

    def assessment_payload(self, lecturer_id):
        values = {
            "lecturer": lecturer_id,
            "course": self.course.id,
            "academic_session": "2026/2027",
            "semester": "First",
        }
        for field in AssessmentReport.INDICATOR_FIELDS:
            values[field] = 4
        return values

    def test_lecturer_profile_assessment_and_summary_endpoints(self):
        response = self.client.post(
            "/api/lecturers/lecturer-profiles/",
            {
                "user": self.lecturer_user.id,
                "department": self.department.id,
                "staff_id": "MTH-001",
                "rank": "Senior Lecturer",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        lecturer_id = response.data["id"]

        response = self.client.post(
            "/api/lecturers/lecturer-profiles/",
            {
                "user": self.lecturer_user.id,
                "department": self.department.id,
                "staff_id": "MTH-002",
                "rank": "Senior Lecturer",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/api/lecturers/assessment-reports/",
            self.assessment_payload(lecturer_id),
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(AssessmentReport.objects.get().student, self.user)
        self.assertEqual(response.data["average_rating"], 4.0)

        invalid_payload = {**self.assessment_payload(lecturer_id), "presents_content_actively": 6}
        response = self.client.post("/api/lecturers/assessment-reports/", invalid_payload, format="json")
        self.assertEqual(response.status_code, 400)

        response = self.client.get(f"/api/lecturers/lecturer-profiles/{lecturer_id}/assessment_summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_assessments"], 1)

        response = self.client.get(
            "/api/lecturers/assessment-reports/",
            {"academic_session": "2026/2027", "semester": "First", "search": "MTH"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_lecturers_require_authentication(self):
        anonymous = APIClient()
        response = anonymous.get("/api/lecturers/lecturer-profiles/")
        self.assertIn(response.status_code, [401, 403])
