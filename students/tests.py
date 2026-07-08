import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from rest_framework.test import APIClient

from core.models import Department, Faculty
from courses.models import Course

from .models import Student, StudentFeedback, StudentFeedbackAttachment, StudentFeedbackUpdate, StudentNotification
from .serializers import StudentFeedbackSerializer


MEDIA_ROOT = tempfile.mkdtemp()


class StudentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            username="dqa_admin",
            email="dqa_admin@example.com",
            password="password",
        )
        self.student_user = get_user_model().objects.create_user(
            username="student_user",
            email="student_user@example.com",
            password="password",
        )
        self.student_user.profile.status = "student"
        self.student_user.profile.save()
        self.faculty = Faculty.objects.create(name="Faculty of Science")
        self.department = Department.objects.create(faculty=self.faculty, name="Computer Science")
        self.other_faculty = Faculty.objects.create(name="Faculty of Arts")
        self.other_department = Department.objects.create(faculty=self.other_faculty, name="History")
        self.course = Course.objects.create(department=self.department, code="CSC 101", title="Introduction to Computing")

    def student_payload(self, **overrides):
        payload = {
            "user": self.student_user.id,
            "matric_number": "CSC/2026/001",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@student.example.com",
            "faculty": self.faculty.id,
            "department": self.department.id,
            "programme": "BSc Computer Science",
            "level": "100",
            "status": "active",
            "courses": [self.course.id],
        }
        payload.update(overrides)
        return payload

    def authenticate_admin(self):
        self.client.force_authenticate(self.admin)

    def authenticate_student(self):
        self.client.force_authenticate(self.student_user)

    def test_student_crud_filtering_and_core_references(self):
        self.authenticate_admin()

        response = self.client.post("/api/students/", self.student_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        student_id = response.data["id"]
        self.assertEqual(response.data["faculty_name"], "Faculty of Science")
        self.assertEqual(response.data["department_name"], "Computer Science")
        self.assertEqual(response.data["course_codes"], ["CSC 101"])
        self.assertEqual(response.data["matric_number"], "CSC/2026/001")

        list_response = self.client.get("/api/students/?department=%s&search=Ada" % self.department.id)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)

        detail_response = self.client.get(f"/api/students/{student_id}/")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["email"], "ada@student.example.com")

        patch_response = self.client.patch(f"/api/students/{student_id}/", {"level": "200"}, format="json")
        self.assertEqual(patch_response.status_code, 200, patch_response.data)
        self.assertEqual(patch_response.data["level"], "200")

        delete_response = self.client.delete(f"/api/students/{student_id}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Student.objects.filter(pk=student_id).exists())

    def test_student_validation_errors(self):
        self.authenticate_admin()

        missing_response = self.client.post("/api/students/", {"first_name": "Ada"}, format="json")
        self.assertEqual(missing_response.status_code, 400)

        bad_department_response = self.client.post(
            "/api/students/",
            self.student_payload(department=self.other_department.id),
            format="json",
        )
        self.assertEqual(bad_department_response.status_code, 400)
        self.assertIn("department", bad_department_response.data)

        bad_course_response = self.client.post(
            "/api/students/",
            self.student_payload(
                matric_number="CSC/2026/002",
                email="badcourse@student.example.com",
                courses=[Course.objects.create(department=self.other_department, code="HIS 101", title="History").id],
            ),
            format="json",
        )
        self.assertEqual(bad_course_response.status_code, 400)
        self.assertIn("courses", bad_course_response.data)

        bad_email_response = self.client.post(
            "/api/students/",
            self.student_payload(matric_number="CSC/2026/003", email="not-an-email"),
            format="json",
        )
        self.assertEqual(bad_email_response.status_code, 400)
        self.assertIn("email", bad_email_response.data)

        bad_matric_response = self.client.post(
            "/api/students/",
            self.student_payload(matric_number="CSC 2026 004", email="badmatric@student.example.com"),
            format="json",
        )
        self.assertEqual(bad_matric_response.status_code, 400)
        self.assertIn("matric_number", bad_matric_response.data)

        self.client.post("/api/students/", self.student_payload(), format="json")
        duplicate_matric_response = self.client.post(
            "/api/students/",
            self.student_payload(user=None, email="duplicate@student.example.com"),
            format="json",
        )
        self.assertEqual(duplicate_matric_response.status_code, 400)
        self.assertIn("matric_number", duplicate_matric_response.data)

        duplicate_email_response = self.client.post(
            "/api/students/",
            self.student_payload(user=None, matric_number="CSC/2026/005"),
            format="json",
        )
        self.assertEqual(duplicate_email_response.status_code, 400)
        self.assertIn("email", duplicate_email_response.data)

    def test_student_permissions(self):
        self.authenticate_admin()
        create_response = self.client.post("/api/students/", self.student_payload(), format="json")
        self.assertEqual(create_response.status_code, 201, create_response.data)
        student_id = create_response.data["id"]

        self.client.logout()
        unauthenticated_response = self.client.get("/api/students/")
        self.assertIn(unauthenticated_response.status_code, [401, 403])

        self.authenticate_student()
        own_list_response = self.client.get("/api/students/")
        self.assertEqual(own_list_response.status_code, 200)
        self.assertEqual(len(own_list_response.data), 1)

        own_detail_response = self.client.get(f"/api/students/{student_id}/")
        self.assertEqual(own_detail_response.status_code, 200)

        forbidden_create_response = self.client.post(
            "/api/students/",
            self.student_payload(user=None, matric_number="CSC/2026/006", email="studentcreate@student.example.com"),
            format="json",
        )
        self.assertEqual(forbidden_create_response.status_code, 403)


class StudentFeedbackApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            username="dqa_admin",
            email="dqa_admin@example.com",
            password="password",
        )
        self.user = get_user_model().objects.create_user(
            username="student_user",
            email="student_user@example.com",
            password="password",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_serializer_accepts_frontend_feedback_fields(self):
        payload = {
            "student": "demo_user",
            "feedback": "This is a test feedback.",
            "category": "complaint",
        }

        serializer = StudentFeedbackSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["student_name"], "demo_user")
        self.assertEqual(serializer.validated_data["feedback_text"], "This is a test feedback.")

    def test_feedback_endpoint_persists_authenticated_user_and_validates_choices(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/students/feedback-tracking/",
            {
                "student": "student_user",
                "feedback": "Lecture room needs better ventilation.",
                "category": "complaint",
                "urgency": "high",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        feedback = StudentFeedback.objects.get()
        self.assertEqual(feedback.submitted_by, self.user)
        self.assertEqual(feedback.status, StudentFeedback.Status.PENDING)
        self.assertEqual(response.data["submitted_by"], self.user.id)

        invalid_response = self.client.post(
            "/api/students/feedback-tracking/",
            {
                "student": "student_user",
                "feedback": "Invalid category test.",
                "category": "unknown",
            },
            format="json",
        )
        self.assertEqual(invalid_response.status_code, 400)

        self.client.logout()
        unauthenticated_response = self.client.get("/api/students/feedback-tracking/")
        self.assertIn(unauthenticated_response.status_code, [401, 403])

    @override_settings(MEDIA_ROOT=MEDIA_ROOT)
    def test_feedback_endpoint_accepts_multipart_attachments(self):
        self.client.force_authenticate(self.user)
        screenshot = SimpleUploadedFile("screenshot.png", b"png-content", content_type="image/png")
        evidence = SimpleUploadedFile("evidence.pdf", b"pdf-content", content_type="application/pdf")

        response = self.client.post(
            "/api/students/feedback-tracking/",
            {
                "student": "student_user",
                "feedback": "Attached evidence for this complaint.",
                "category": "complaint",
                "classification": "academic",
                "urgency": "normal",
                "submission_mode": "open_identity",
                "attachments": [screenshot, evidence],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.data)
        feedback = StudentFeedback.objects.get()
        self.assertEqual(feedback.attachments.count(), 2)
        self.assertEqual(StudentFeedbackAttachment.objects.filter(uploaded_by=self.user).count(), 2)
        self.assertEqual(len(response.data["attachments"]), 2)
        self.assertEqual(response.data["attachments"][0]["original_name"], "screenshot.png")
        self.assertIn("url", response.data["attachments"][0])

    @override_settings(MEDIA_ROOT=MEDIA_ROOT)
    def test_feedback_endpoint_rejects_invalid_attachments(self):
        self.client.force_authenticate(self.user)

        bad_type_response = self.client.post(
            "/api/students/feedback-tracking/",
            {
                "student": "student_user",
                "feedback": "Invalid extension.",
                "category": "complaint",
                "attachments": [
                    SimpleUploadedFile("malware.exe", b"bad", content_type="application/octet-stream"),
                ],
            },
            format="multipart",
        )
        self.assertEqual(bad_type_response.status_code, 400)
        self.assertIn("attachments", bad_type_response.data)

        oversized_response = self.client.post(
            "/api/students/feedback-tracking/",
            {
                "student": "student_user",
                "feedback": "Oversized file.",
                "category": "complaint",
                "attachments": [
                    SimpleUploadedFile("large.pdf", b"x" * (1024 * 1024 + 1), content_type="application/pdf"),
                ],
            },
            format="multipart",
        )
        self.assertEqual(oversized_response.status_code, 400)
        self.assertIn("attachments", oversized_response.data)

    def test_feedback_permissions_filter_non_manager_records(self):
        other_user = get_user_model().objects.create_user(username="other_student", password="password")
        StudentFeedback.objects.create(
            submitted_by=self.user,
            student_name="student_user",
            feedback_text="My feedback",
            category="suggestion",
        )
        StudentFeedback.objects.create(
            submitted_by=other_user,
            student_name="other_student",
            feedback_text="Other feedback",
            category="inquiry",
        )

        self.client.force_authenticate(self.user)
        student_response = self.client.get("/api/students/feedback/")
        self.assertEqual(student_response.status_code, 200)
        self.assertEqual(len(student_response.data), 1)

        self.client.force_authenticate(self.admin)
        admin_response = self.client.get("/api/students/feedback/")
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(len(admin_response.data), 2)

    def test_admin_update_creates_complaint_timeline_and_student_notification(self):
        complaint = StudentFeedback.objects.create(
            submitted_by=self.user,
            student_name="student_user",
            feedback_text="The lecture room needs repair.",
            category="complaint",
        )
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/students/feedback/{complaint.id}/",
            {
                "status": "under_review",
                "admin_comment": "We are reviewing this with the department.",
                "assigned_to": self.admin.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, StudentFeedback.Status.UNDER_REVIEW)
        self.assertEqual(complaint.admin_comment, "We are reviewing this with the department.")
        self.assertEqual(complaint.updated_by, self.admin)
        self.assertEqual(StudentFeedbackUpdate.objects.filter(complaint=complaint).count(), 1)
        notification = StudentNotification.objects.get(complaint=complaint)
        self.assertEqual(notification.user, self.user)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.title, "Complaint Updated")
        self.assertIn("Under Review", notification.message)
        self.assertEqual(response.data["updates"][0]["new_status"], "under_review")
        self.assertEqual(response.data["notification_history"][0]["title"], "Complaint Updated")

        self.client.force_authenticate(self.user)
        list_response = self.client.get("/api/students/notifications/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 1)

        mark_read_response = self.client.post(f"/api/students/notifications/{notification.id}/mark-read/")
        self.assertEqual(mark_read_response.status_code, 200, mark_read_response.data)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_student_cannot_set_admin_complaint_fields(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/students/feedback-tracking/",
            {
                "student": "student_user",
                "feedback": "I want to close this myself.",
                "category": "complaint",
                "status": "resolved",
                "admin_comment": "Not allowed",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)
        self.assertIn("admin_comment", response.data)

    def test_complaint_update_permission_edges_by_role(self):
        manager_roles = ["admin", "principle_officer", "focal_person"]
        blocked_roles = ["student", "department_admin", "faculty_admin", "committee_member", "read_only_viewer", "unknown_role"]

        for role in manager_roles:
            complaint = StudentFeedback.objects.create(
                submitted_by=self.user,
                student_name=f"{role}_complainant",
                feedback_text="Complaint requiring staff update.",
                category="complaint",
            )
            staff = get_user_model().objects.create_user(username=f"{role}_staff", password="password")
            staff.profile.status = role
            staff.profile.save()
            self.client.force_authenticate(staff)

            with self.subTest(role=role, expected="can_update"):
                response = self.client.patch(
                    f"/api/students/feedback/{complaint.id}/",
                    {"status": "in_progress", "admin_comment": f"Handled by {role}."},
                    format="json",
                )
                self.assertEqual(response.status_code, 200, response.data)
                self.assertTrue(StudentNotification.objects.filter(complaint=complaint, user=self.user).exists())

        for role in blocked_roles:
            complaint = StudentFeedback.objects.create(
                submitted_by=self.user,
                student_name=f"{role}_complainant",
                feedback_text="Complaint requiring restricted update.",
                category="complaint",
            )
            actor = get_user_model().objects.create_user(username=f"{role}_actor", password="password")
            actor.profile.status = role
            actor.profile.save()
            self.client.force_authenticate(actor)

            with self.subTest(role=role, expected="blocked_update"):
                response = self.client.patch(
                    f"/api/students/feedback/{complaint.id}/",
                    {"status": "resolved", "admin_comment": "Should not be allowed."},
                    format="json",
                )
                self.assertIn(response.status_code, [403, 404])

        self.client.force_authenticate(self.user)
        own_response = self.client.get("/api/students/feedback/")
        self.assertEqual(own_response.status_code, 200)
