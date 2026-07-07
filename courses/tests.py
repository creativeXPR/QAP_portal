from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Department, Faculty
from .models import Course, LectureSession


class CoursesApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="course_user", password="password")
        self.client.force_authenticate(self.user)
        self.faculty = Faculty.objects.create(name="Faculty of Science")
        self.department = Department.objects.create(faculty=self.faculty, name="Computer Science")

    def test_course_and_lecture_session_endpoints(self):
        response = self.client.post(
            "/api/courses/courses/",
            {"department": self.department.id, "code": "CSC 101", "title": "Introduction to Computing"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        course_id = response.data["id"]

        response = self.client.post(
            "/api/courses/courses/",
            {"department": self.department.id, "code": "CSC 101", "title": "Duplicate"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        payload = {
            "course": course_id,
            "monitored_at": "2026-07-07T10:00:00Z",
            "time_slot": "10:00-11:00",
            "level": "100",
            "mode": "physical",
            "lecturer_present": "yes",
            "actual_duration": "45-60",
            "venue": "Room A",
            "held": True,
            "reason_not_held": "",
            "estimated_attendance": "100-500",
            "classroom_environment_rating": 4,
            "teaching_effectiveness_rating": 5,
            "quality_concerns": "",
        }
        response = self.client.post("/api/courses/lecture-sessions/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(LectureSession.objects.get().respondent, self.user)

        invalid_payload = {**payload, "held": False, "reason_not_held": ""}
        response = self.client.post("/api/courses/lecture-sessions/", invalid_payload, format="json")
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/api/courses/lecture-sessions/", {"held": True, "search": "CSC"})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_courses_require_authentication(self):
        anonymous = APIClient()
        response = anonymous.get("/api/courses/courses/")
        self.assertIn(response.status_code, [401, 403])
