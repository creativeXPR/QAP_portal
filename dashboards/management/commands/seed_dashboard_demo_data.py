from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accreditation.models import (
    AccreditationComponent,
    AccreditationCycle,
    AccreditationMetric,
    ComponentScore,
    CorrectiveAction,
    EarlyWarningAlert,
    MetricSubmission,
    PARIResult,
)
from core.models import Department, Faculty
from courses.models import Course, LectureSession
from documents.models import InstitutionalDocument, InstitutionalDocumentCategory
from examinations.models import ExamQualityReport, ExamSession
from lecturers.models import AssessmentReport, LecturerProfile
from qa_committee.models import (
    CommitteeMeeting,
    QAActionEvidence,
    QAActionPlan,
    QAAuditCycle,
    QAAuditFinding,
    QACommittee,
    QACommitteeDataReview,
    QACommitteeMember,
    QACommitteeReport,
    QARecommendation,
)
from qa_committee.services import get_committee_effectiveness_score
from students.models import Student, StudentFeedback, StudentFeedbackUpdate, StudentNotification


class Command(BaseCommand):
    help = "Seed realistic demo data across modules for dashboard and QA Committee testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="StrongPass123!",
            help="Password assigned to created demo users.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        today = timezone.localdate()
        now = timezone.now()

        users = self.create_users(password)
        faculty, department, other_faculty, other_department = self.create_core_data()
        courses = self.create_courses(department, other_department)
        self.create_students(users, faculty, department, courses)
        self.create_course_and_lecturer_data(users, department, courses, now)
        self.create_exam_data(users, department, courses, today)
        self.create_documents(users)
        cycle, component = self.create_accreditation_data(users, faculty, department, courses, today)
        self.create_student_complaints(users)
        self.create_qa_committee_data(users, faculty, department, cycle, component, today, now)

        self.stdout.write(self.style.SUCCESS("Dashboard demo data seeded successfully."))
        self.stdout.write(
            "Created/updated demo users: "
            + ", ".join(f"{username} / {password}" for username in sorted(users))
        )
        self.stdout.write(f"Dashboard URL: /api/dashboards/summary/")

    def create_users(self, password):
        User = get_user_model()
        roles = {
            "demo_admin": "admin",
            "demo_focal": "focal_person",
            "demo_principal": "principle_officer",
            "demo_student": "student",
            "demo_committee_secretary": "committee_secretary",
            "demo_department_admin": "department_admin",
            "demo_readonly": "read_only_viewer",
        }
        users = {}
        for username, role in roles.items():
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
            user.profile.status = role
            user.profile.profile_complete = True
            user.profile.save()
            users[username] = user
        return users

    def create_core_data(self):
        faculty, _ = Faculty.objects.get_or_create(name="Faculty of Science")
        department, _ = Department.objects.get_or_create(faculty=faculty, name="Computer Science")
        other_faculty, _ = Faculty.objects.get_or_create(name="Faculty of Arts")
        other_department, _ = Department.objects.get_or_create(faculty=other_faculty, name="History")
        return faculty, department, other_faculty, other_department

    def create_courses(self, department, other_department):
        course_specs = [
            (department, "CSC 101", "Introduction to Computing"),
            (department, "CSC 201", "Data Structures"),
            (department, "CSC 401", "Software Quality Assurance"),
            (other_department, "HIS 101", "Introduction to Nigerian History"),
        ]
        courses = {}
        for dept, code, title in course_specs:
            course, _ = Course.objects.update_or_create(
                code=code,
                defaults={"department": dept, "title": title},
            )
            courses[code] = course
        return courses

    def create_students(self, users, faculty, department, courses):
        student, _ = Student.objects.update_or_create(
            matric_number="CSC/2026/001",
            defaults={
                "user": users["demo_student"],
                "faculty": faculty,
                "department": department,
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada.lovelace@student.example.com",
                "programme": "BSc Computer Science",
                "level": "400",
                "status": "active",
            },
        )
        student.courses.set([courses["CSC 101"], courses["CSC 201"], courses["CSC 401"]])

        dept_admin, _ = Student.objects.update_or_create(
            matric_number="CSC/STAFF/001",
            defaults={
                "user": users["demo_department_admin"],
                "faculty": faculty,
                "department": department,
                "first_name": "Department",
                "last_name": "Admin",
                "email": "department.admin@example.com",
                "programme": "BSc Computer Science",
                "level": "PG",
                "status": "active",
            },
        )
        dept_admin.courses.set([courses["CSC 401"]])

    def create_course_and_lecturer_data(self, users, department, courses, now):
        for days_ago, course_code, held, rating in [
            (5, "CSC 101", True, 5),
            (4, "CSC 201", True, 4),
            (3, "CSC 401", False, 2),
        ]:
            LectureSession.objects.update_or_create(
                course=courses[course_code],
                monitored_at=now - timedelta(days=days_ago),
                defaults={
                    "respondent": users["demo_focal"],
                    "time_slot": "10:00-11:00",
                    "level": "400" if course_code == "CSC 401" else "100",
                    "mode": "physical",
                    "lecturer_present": "yes" if held else "no",
                    "actual_duration": ">60" if held else "<30",
                    "venue": "DQA Demo Lecture Theatre",
                    "held": held,
                    "reason_not_held": "" if held else "lecturer_absent",
                    "estimated_attendance": "100-500",
                    "classroom_environment_rating": rating,
                    "teaching_effectiveness_rating": rating,
                    "quality_concerns": "" if held else "Lecturer absent and class did not hold.",
                },
            )

        lecturer_user = users["demo_focal"]
        profile = LecturerProfile.objects.filter(staff_id="DEMO-LECT-001").first()
        if profile is None:
            profile, _ = LecturerProfile.objects.update_or_create(
                user=lecturer_user,
                defaults={"department": department, "staff_id": "DEMO-LECT-001", "rank": "Senior Lecturer"},
            )
        else:
            profile.department = department
            profile.rank = "Senior Lecturer"
            profile.save(update_fields=["department", "rank"])
        report = AssessmentReport.objects.filter(lecturer=profile, course=courses["CSC 401"], student=users["demo_student"]).first()
        if report is None:
            payload = {
                "lecturer": profile,
                "student": users["demo_student"],
                "course": courses["CSC 401"],
                "academic_session": "2025/2026",
                "semester": "First",
            }
            for field in AssessmentReport.INDICATOR_FIELDS:
                payload[field] = 4
            AssessmentReport.objects.create(**payload)

    def create_exam_data(self, users, department, courses, today):
        exam, _ = ExamSession.objects.update_or_create(
            department=department,
            course_code_title=f"{courses['CSC 401'].code} - {courses['CSC 401'].title}",
            exam_date=today - timedelta(days=7),
            defaults={
                "venue": "DQA Demo Exam Hall",
                "academic_session": "First Semester 2025/2026",
            },
        )
        if not ExamQualityReport.objects.filter(exam_session=exam, student=users["demo_student"]).exists():
            rating_fields = {
                "adequacy_of_seating": 4,
                "lighting_conditions": 4,
                "ventilation_room_comfort": 3,
                "noise_free_environment": 4,
                "accessibility_suitability_of_venue": 4,
                "invigilators_arrived_on_time": 5,
                "clear_communication_of_instructions": 4,
                "professional_conduct_of_invigilators": 5,
                "fair_consistent_enforcement_of_rules": 4,
                "responsiveness_to_student_needs": 4,
                "prompt_start_of_examination": 4,
                "organized_distribution_of_materials": 4,
                "proper_management_of_exam_time": 4,
                "orderliness_during_submission": 5,
                "overall_rating": 4,
            }
            ExamQualityReport.objects.create(
                exam_session=exam,
                student=users["demo_student"],
                observed_misconduct=False,
                incident_description="",
                action_taken="",
                suggestions_for_improvement="Improve ventilation before next examination.",
                **rating_fields,
            )

    def create_documents(self, users):
        category, _ = InstitutionalDocumentCategory.objects.update_or_create(
            slug="qa-policy-documents",
            defaults={"name": "QA Policy Documents", "description": "Demo quality assurance policy documents.", "is_active": True},
        )
        InstitutionalDocument.objects.update_or_create(
            slug="demo-quality-assurance-policy",
            defaults={
                "title": "Demo Quality Assurance Policy",
                "category": category,
                "document_type": "link",
                "description": "Demo policy document for dashboard testing.",
                "related_module": "institutional_policy",
                "visibility_level": "all_authenticated",
                "status": "published",
                "owner": "Directorate of Quality Assurance",
                "uploaded_by": users["demo_admin"],
                "published_by": users["demo_admin"],
                "published_at": timezone.now(),
                "is_latest": True,
                "is_active": True,
            },
        )

    def create_accreditation_data(self, users, faculty, department, courses, today):
        cycle, _ = AccreditationCycle.objects.update_or_create(
            title="Demo NUC Accreditation Readiness Cycle",
            academic_session="2025/2026",
            programme="BSc Computer Science",
            defaults={
                "faculty": faculty.name,
                "department": department.name,
                "start_date": today - timedelta(days=60),
                "submission_deadline": today + timedelta(days=30),
                "internal_review_deadline": today + timedelta(days=14),
                "status": "submission_open",
            },
        )
        component, _ = AccreditationComponent.objects.update_or_create(
            code="staffing",
            defaults={
                "name": "Academic Staffing",
                "description": "Staffing strength and qualification readiness.",
                "weight": Decimal("25.00"),
                "is_active": True,
            },
        )
        metric, _ = AccreditationMetric.objects.update_or_create(
            component=component,
            code="student_staff_ratio",
            defaults={
                "name": "Student Staff Ratio",
                "value_type": "numeric",
                "unit": "ratio",
                "minimum_benchmark": Decimal("1.00"),
                "warning_threshold": Decimal("30.00"),
                "danger_threshold": Decimal("45.00"),
                "required_evidence": True,
                "is_active": True,
            },
        )
        MetricSubmission.objects.update_or_create(
            cycle=cycle,
            programme="BSc Computer Science",
            component=component,
            metric=metric,
            reporting_period="2025/2026 Q1",
            defaults={
                "submitted_value": "34",
                "numeric_value": Decimal("34.0000"),
                "source_unit": department.name,
                "submitted_by": users["demo_focal"],
                "validation_status": "validated",
            },
        )
        ComponentScore.objects.update_or_create(
            cycle=cycle,
            programme="BSc Computer Science",
            component=component,
            defaults={
                "score": Decimal("74.00"),
                "status": "warning",
                "metrics": {"student_staff_ratio": 34},
                "calculated_by": users["demo_admin"],
            },
        )
        PARIResult.objects.update_or_create(
            cycle=cycle,
            programme="BSc Computer Science",
            defaults={
                "pari_score": Decimal("78.50"),
                "classification": "moderate_risk",
                "breakdown": [{"component": "staffing", "score": 74}],
                "calculated_by": users["demo_admin"],
            },
        )
        alert, _ = EarlyWarningAlert.objects.update_or_create(
            cycle=cycle,
            programme="BSc Computer Science",
            component=component,
            trigger_type="staff_shortage",
            defaults={
                "severity": "critical",
                "message": "Student-staff ratio is above internal benchmark.",
                "status": "open",
            },
        )
        CorrectiveAction.objects.update_or_create(
            cycle=cycle,
            programme="BSc Computer Science",
            component=component,
            alert=alert,
            title="Recruit adjunct lecturers",
            defaults={
                "description": "Recruit qualified adjunct lecturers for high-enrolment courses.",
                "assigned_unit": department.name,
                "responsible_officer": "Head of Department",
                "priority": "high",
                "deadline": today + timedelta(days=21),
                "progress_percentage": 45,
                "status": "in_progress",
            },
        )
        return cycle, component

    def create_student_complaints(self, users):
        complaint, _ = StudentFeedback.objects.update_or_create(
            submitted_by=users["demo_student"],
            student_name="demo_student",
            feedback_text="Lecture room needs better ventilation.",
            defaults={
                "student_email": users["demo_student"].email,
                "category": "complaint",
                "classification": "facility",
                "status": "under_review",
                "urgency": "high",
                "admin_comment": "Facilities team has been notified.",
                "assigned_to": users["demo_department_admin"],
                "updated_by": users["demo_admin"],
            },
        )
        StudentFeedbackUpdate.objects.get_or_create(
            complaint=complaint,
            previous_status="pending",
            new_status="under_review",
            defaults={
                "admin_comment": "Facilities team has been notified.",
                "assigned_to": users["demo_department_admin"],
                "updated_by": users["demo_admin"],
            },
        )
        StudentNotification.objects.get_or_create(
            user=users["demo_student"],
            complaint=complaint,
            title="Complaint Updated",
            defaults={
                "message": "Your complaint is now Under Review.",
                "notification_type": "complaint_update",
                "is_read": False,
            },
        )

    def create_qa_committee_data(self, users, faculty, department, cycle, component, today, now):
        committee, _ = QACommittee.objects.update_or_create(
            name="Faculty of Science QA Committee",
            defaults={
                "scope_type": "faculty",
                "faculty": faculty,
                "department": None,
                "programme": "",
                "description": "Faculty-level committee for continuous quality monitoring.",
                "status": "active",
                "date_constituted": today - timedelta(days=120),
                "created_by": users["demo_admin"],
            },
        )
        QACommitteeMember.objects.get_or_create(
            committee=committee,
            user=users["demo_admin"],
            defaults={"role": "chairperson", "designation": "DQA Admin", "start_date": today - timedelta(days=120), "is_active": True},
        )
        QACommitteeMember.objects.get_or_create(
            committee=committee,
            user=users["demo_committee_secretary"],
            defaults={"role": "secretary", "designation": "Committee Secretary", "start_date": today - timedelta(days=120), "is_active": True},
        )
        meeting, _ = CommitteeMeeting.objects.update_or_create(
            committee=committee,
            title="Demo Quarterly Quality Review",
            defaults={
                "meeting_type": "quarterly_review",
                "scheduled_date": now - timedelta(days=10),
                "held_date": now - timedelta(days=10),
                "venue": "DQA Conference Room",
                "agenda": "Review accreditation readiness, complaints, documents, and teaching delivery.",
                "minutes": "Committee reviewed risk areas and assigned corrective actions.",
                "status": "held",
                "created_by": users["demo_admin"],
            },
        )
        audit, _ = QAAuditCycle.objects.update_or_create(
            committee=committee,
            title="Demo Faculty Q1 Audit",
            defaults={
                "review_period_start": today - timedelta(days=90),
                "review_period_end": today,
                "audit_type": "accreditation_readiness",
                "target_faculty": faculty,
                "target_department": department,
                "target_programme": "BSc Computer Science",
                "status": "submitted",
                "created_by": users["demo_admin"],
            },
        )
        finding, _ = QAAuditFinding.objects.update_or_create(
            audit_cycle=audit,
            title="Staffing benchmark below target",
            defaults={
                "source_module": "accreditation",
                "source_record_type": "ComponentScore",
                "source_record_id": str(component.id),
                "description": "Staffing component score indicates moderate accreditation risk.",
                "category": "staffing",
                "severity": "critical",
                "risk_level": "high",
                "evidence_summary": "Referenced from demo accreditation component score.",
                "status": "open",
                "created_by": users["demo_admin"],
            },
        )
        recommendation, _ = QARecommendation.objects.update_or_create(
            audit_cycle=audit,
            finding=finding,
            title="Strengthen staffing before accreditation visit",
            defaults={
                "recommendation_text": "Recruit adjunct lecturers and submit workload redistribution plan.",
                "responsible_unit_type": "department",
                "responsible_faculty": faculty,
                "responsible_department": department,
                "assigned_to": users["demo_department_admin"],
                "priority": "urgent",
                "due_date": today + timedelta(days=30),
                "status": "in_progress",
                "created_by": users["demo_admin"],
            },
        )
        action, _ = QAActionPlan.objects.update_or_create(
            recommendation=recommendation,
            action_description="Prepare recruitment memo and teaching workload redistribution plan.",
            defaults={
                "owner": users["demo_department_admin"],
                "expected_completion_date": today + timedelta(days=21),
                "actual_completion_date": None,
                "progress_percentage": 65,
                "status": "in_progress",
                "implementation_notes": "Draft memo prepared and pending faculty review.",
            },
        )
        QAActionEvidence.objects.update_or_create(
            action_plan=action,
            title="Recruitment memo evidence link",
            defaults={
                "description": "Link to memo draft for committee verification.",
                "external_url": "https://example.com/demo/recruitment-memo",
                "uploaded_by": users["demo_department_admin"],
                "verification_status": "pending",
            },
        )
        report, _ = QACommitteeReport.objects.update_or_create(
            committee=committee,
            audit_cycle=audit,
            report_type="quarterly",
            reporting_period_start=today - timedelta(days=90),
            reporting_period_end=today,
            defaults={
                "summary": "Demo quarterly QA report covering staffing, complaints, and documents.",
                "key_findings": "Staffing benchmark and facility complaint require follow-up.",
                "recommendations_summary": "Recruit adjunct lecturers and resolve facility issue.",
                "action_plan_summary": "Action plan is in progress with evidence pending verification.",
                "status": "submitted",
                "submitted_by": users["demo_admin"],
                "submitted_at": now,
            },
        )
        report.qacei_score = get_committee_effectiveness_score(committee)
        report.save(update_fields=["qacei_score", "updated_at"])
        QACommitteeDataReview.objects.update_or_create(
            committee=committee,
            review_title="Demo lecture delivery and accreditation data review",
            source_module="courses",
            defaults={
                "source_endpoint_or_model": "LectureSession",
                "target_faculty": faculty,
                "target_department": department,
                "target_programme": "BSc Computer Science",
                "review_period_start": today - timedelta(days=90),
                "review_period_end": today,
                "extracted_summary": {"scheduled_lectures": 3, "held_lectures": 2, "delivery_rate": 66.67},
                "validation_status": "questionable",
                "reviewer": users["demo_admin"],
                "reviewer_comment": "One monitored lecture did not hold and needs follow-up.",
            },
        )
