from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accreditation.models import (
    AccreditationComponent,
    AccreditationCycle,
    ComponentScore,
    CorrectiveAction,
    EarlyWarningAlert,
    Evidence,
    PARIResult,
)
from core.models import Department, Faculty
from courses.models import Course, LectureSession
from documents.models import InstitutionalDocument, InstitutionalDocumentCategory
from examinations.models import ExamQualityReport, ExamSession
from students.models import Student, StudentFeedback

from .services import percentage


class DashboardApiTests(TestCase):
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
        self.department_admin = get_user_model().objects.create_user(
            username="department_admin",
            email="department_admin@example.com",
            password="password",
        )
        self.department_admin.profile.status = "department_admin"
        self.department_admin.profile.save()
        self.faculty = Faculty.objects.create(name="Faculty of Science")
        self.department = Department.objects.create(faculty=self.faculty, name="Computer Science")
        self.other_faculty = Faculty.objects.create(name="Faculty of Arts")
        self.other_department = Department.objects.create(faculty=self.other_faculty, name="History")
        self.course = Course.objects.create(department=self.department, code="CSC 101", title="Introduction")
        Student.objects.create(
            user=self.department_admin,
            faculty=self.faculty,
            department=self.department,
            matric_number="CSC/2026/900",
            first_name="Dept",
            last_name="Admin",
            email="deptadmin@student.example.com",
            programme="BSc Computer Science",
            level="400",
        )
        self.seed_dashboard_data()

    def seed_dashboard_data(self):
        self.cycle = AccreditationCycle.objects.create(
            title="NUC Cycle",
            academic_session="2025/2026",
            faculty=self.faculty.name,
            department=self.department.name,
            programme="BSc Computer Science",
            start_date=timezone.localdate() - timedelta(days=10),
            submission_deadline=timezone.localdate() + timedelta(days=10),
            status="submission_open",
        )
        self.component = AccreditationComponent.objects.create(
            name="Academic Staffing Monitoring",
            code="staffing",
            weight=25,
        )
        PARIResult.objects.create(
            cycle=self.cycle,
            programme="BSc Computer Science",
            pari_score=82,
            classification="accreditation_ready",
            calculated_by=self.admin,
        )
        ComponentScore.objects.create(
            cycle=self.cycle,
            programme="BSc Computer Science",
            component=self.component,
            score=74,
            status="warning",
            calculated_by=self.admin,
        )
        EarlyWarningAlert.objects.create(
            cycle=self.cycle,
            programme="BSc Computer Science",
            component=self.component,
            trigger_type="staff_shortage",
            severity="critical",
            message="Staffing below benchmark",
        )
        CorrectiveAction.objects.create(
            cycle=self.cycle,
            programme="BSc Computer Science",
            component=self.component,
            title="Recruit lecturers",
            description="Recruit more lecturers.",
            deadline=timezone.localdate() - timedelta(days=1),
        )
        Evidence.objects.create(
            cycle=self.cycle,
            programme="BSc Computer Science",
            component=self.component,
            title="Staff list",
            evidence_type="staffing",
            file=SimpleUploadedFile("staff.pdf", b"%PDF-1.4"),
            uploaded_by=self.admin,
        )
        LectureSession.objects.create(
            course=self.course,
            respondent=self.admin,
            monitored_at=timezone.now(),
            time_slot="10:00-11:00",
            level="100",
            mode="physical",
            lecturer_present="yes",
            actual_duration=">60",
            venue="Room A",
            held=True,
            estimated_attendance="<100",
            classroom_environment_rating=4,
            teaching_effectiveness_rating=5,
        )
        exam_session = ExamSession.objects.create(
            department=self.department,
            course_code_title="CSC 101",
            exam_date=timezone.localdate(),
            venue="Hall A",
            academic_session="2025/2026",
        )
        ExamQualityReport.objects.create(
            exam_session=exam_session,
            student=self.student_user,
            adequacy_of_seating=4,
            lighting_conditions=4,
            ventilation_room_comfort=4,
            noise_free_environment=4,
            accessibility_suitability_of_venue=4,
            invigilators_arrived_on_time=4,
            clear_communication_of_instructions=4,
            professional_conduct_of_invigilators=4,
            fair_consistent_enforcement_of_rules=4,
            responsiveness_to_student_needs=4,
            prompt_start_of_examination=4,
            organized_distribution_of_materials=4,
            proper_management_of_exam_time=4,
            orderliness_during_submission=4,
            observed_misconduct=False,
            overall_rating=4,
        )
        category = InstitutionalDocumentCategory.objects.create(name="Policy Documents")
        InstitutionalDocument.objects.create(
            title="QA Policy",
            category=category,
            document_type="link",
            related_module="institutional_policy",
            visibility_level="all_authenticated",
            status="published",
            uploaded_by=self.admin,
        )
        StudentFeedback.objects.create(
            submitted_by=self.student_user,
            student_name="student_user",
            feedback_text="Good teaching",
            category="suggestion",
            urgency="normal",
        )

    def authenticate_admin(self):
        self.client.force_authenticate(self.admin)

    def test_summary_endpoint_returns_dashboard_structure(self):
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/summary/")
        self.assertEqual(response.status_code, 200, response.data)
        data = response.data["data"]
        self.assertIn("kpi_cards", data)
        self.assertIn("charts", data)
        self.assertIn("alerts", data)
        self.assertIn("recent_activity", data)
        self.assertTrue(data["kpi_cards"])

    def test_university_overview_returns_kpis(self):
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/university-overview/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["kpis"]["total_faculties"], 2)
        self.assertEqual(response.data["data"]["kpis"]["programmes_accreditation_ready"], 1)

    def test_accreditation_dashboard_handles_missing_module(self):
        self.authenticate_admin()
        with patch("dashboards.services.safe_model_import", return_value=None):
            response = self.client.get("/api/dashboards/accreditation/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["status"], "module_not_available")

    def test_qa_committee_dashboard_returns_missing_module_status(self):
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/qa-committee/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["module_status"]["status"], "module_not_available")

    def test_teaching_learning_handles_missing_lectures_module(self):
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/teaching-learning/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("average_lecture_delivery_rate", response.data["data"])

    def test_examination_dashboard_handles_zero_division(self):
        ExamQualityReport.objects.all().delete()
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/examinations/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["malpractice_rate"], 0)

    def test_documents_dashboard_empty_arrays_when_no_documents_exist(self):
        InstitutionalDocument.objects.all().delete()
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/documents/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["documents_by_category"], [])

    def test_early_warning_dashboard_returns_risk_distribution(self):
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/early-warning/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("risk_category_distribution_pie", response.data["data"]["charts"])

    def test_activity_feed_returns_list_format(self):
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/activity-feed/?limit=5")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsInstance(response.data["data"], list)
        self.assertLessEqual(len(response.data["data"]), 5)

    def test_date_range_and_faculty_filters_work(self):
        self.authenticate_admin()
        response = self.client.get(
            f"/api/dashboards/university-overview/?faculty_id={self.faculty.id}&period=this_year"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["kpis"]["total_departments"], 1)

    def test_permission_restrictions(self):
        response = self.client.get("/api/dashboards/summary/")
        self.assertIn(response.status_code, [401, 403])

        self.client.force_authenticate(self.student_user)
        response = self.client.get("/api/dashboards/summary/")
        self.assertEqual(response.status_code, 403)

    def test_super_admin_can_access_all_dashboard_endpoints(self):
        self.authenticate_admin()
        for endpoint in [
            "summary",
            "university-overview",
            "accreditation",
            "qa-committee",
            "teaching-learning",
            "examinations",
            "documents",
            "student-experience",
            "infrastructure-labs",
            "research",
            "early-warning",
            "activity-feed",
        ]:
            response = self.client.get(f"/api/dashboards/{endpoint}/")
            self.assertEqual(response.status_code, 200, endpoint)

    def test_department_admin_cannot_access_unrelated_department_dashboard(self):
        self.client.force_authenticate(self.department_admin)
        response = self.client.get(f"/api/dashboards/summary/?department_id={self.other_department.id}")
        self.assertEqual(response.status_code, 403)

        own_response = self.client.get(f"/api/dashboards/summary/?department_id={self.department.id}")
        self.assertEqual(own_response.status_code, 200, own_response.data)

    def test_chart_responses_follow_frontend_ready_shape(self):
        self.authenticate_admin()
        response = self.client.get("/api/dashboards/accreditation/")
        chart = response.data["data"]["charts"]["readiness_distribution_pie"]
        self.assertEqual(chart["type"], "pie")
        self.assertIn("labels", chart)
        self.assertIn("datasets", chart)

    def test_percentage_helper_handles_denominator_zero(self):
        self.assertEqual(percentage(10, 0), 0)
