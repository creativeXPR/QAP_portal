from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class QACommittee(TimeStampedModel):
    class ScopeType(models.TextChoices):
        DEPARTMENT = "department", "Department"
        FACULTY = "faculty", "Faculty"
        PROGRAMME = "programme", "Programme"
        INSTITUTIONAL = "institutional", "Institutional"
        UNIT = "unit", "Unit"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        DISSOLVED = "dissolved", "Dissolved"

    name = models.CharField(max_length=255)
    scope_type = models.CharField(max_length=30, choices=ScopeType.choices)
    faculty = models.ForeignKey("core.Faculty", null=True, blank=True, related_name="qa_committees", on_delete=models.PROTECT)
    department = models.ForeignKey("core.Department", null=True, blank=True, related_name="qa_committees", on_delete=models.PROTECT)
    programme = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    date_constituted = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="created_qa_committees", on_delete=models.SET_NULL)

    class Meta:
        ordering = ["name"]

    def clean(self):
        errors = {}
        if self.scope_type == self.ScopeType.DEPARTMENT and not self.department_id:
            errors["department"] = "Department-level committee requires a department."
        if self.scope_type == self.ScopeType.FACULTY and not self.faculty_id:
            errors["faculty"] = "Faculty-level committee requires a faculty."
        if self.scope_type == self.ScopeType.PROGRAMME and not self.programme:
            errors["programme"] = "Programme-level committee requires a programme."
        if self.department_id and self.faculty_id and self.department.faculty_id != self.faculty_id:
            errors["department"] = "Department must belong to the selected faculty."
        if self.status == self.Status.ACTIVE:
            duplicate = QACommittee.objects.filter(
                scope_type=self.scope_type,
                faculty=self.faculty,
                department=self.department,
                programme=self.programme,
                status=self.Status.ACTIVE,
            ).exclude(pk=self.pk)
            if duplicate.exists():
                errors["scope_type"] = "An active committee already exists for this scope."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class QACommitteeMember(TimeStampedModel):
    class Role(models.TextChoices):
        CHAIRPERSON = "chairperson", "Chairperson"
        SECRETARY = "secretary", "Secretary"
        MEMBER = "member", "Member"
        QA_FOCAL_PERSON = "qa_focal_person", "QA Focal Person"
        OBSERVER = "observer", "Observer"

    committee = models.ForeignKey(QACommittee, related_name="members", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="qa_committee_memberships", on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=Role.choices)
    designation = models.CharField(max_length=160, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["committee", "role", "user__username"]
        constraints = [
            models.UniqueConstraint(fields=["committee", "user"], name="unique_committee_user_membership"),
        ]

    def clean(self):
        errors = {}
        if self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date cannot be before start date."
        if self.is_active and self.role in {self.Role.CHAIRPERSON, self.Role.SECRETARY}:
            duplicate = QACommitteeMember.objects.filter(
                committee=self.committee,
                role=self.role,
                is_active=True,
            ).exclude(pk=self.pk)
            if duplicate.exists():
                errors["role"] = f"Only one active {self.role} is allowed per committee."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.role} ({self.committee})"


class CommitteeMeeting(TimeStampedModel):
    class MeetingType(models.TextChoices):
        REGULAR = "regular", "Regular"
        EMERGENCY = "emergency", "Emergency"
        ACCREDITATION_REVIEW = "accreditation_review", "Accreditation Review"
        AUDIT_REVIEW = "audit_review", "Audit Review"
        QUARTERLY_REVIEW = "quarterly_review", "Quarterly Review"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        HELD = "held", "Held"
        CANCELLED = "cancelled", "Cancelled"
        POSTPONED = "postponed", "Postponed"

    committee = models.ForeignKey(QACommittee, related_name="meetings", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    meeting_type = models.CharField(max_length=40, choices=MeetingType.choices, default=MeetingType.REGULAR)
    scheduled_date = models.DateTimeField()
    held_date = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=255, blank=True)
    agenda = models.TextField(blank=True)
    minutes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="created_committee_meetings", on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-scheduled_date"]

    def mark_held(self, held_date=None):
        self.status = self.Status.HELD
        self.held_date = held_date or timezone.now()
        self.save(update_fields=["status", "held_date", "updated_at"])

    def __str__(self):
        return self.title


class CommitteeMeetingAttendance(models.Model):
    class AttendanceStatus(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        EXCUSED = "excused", "Excused"

    meeting = models.ForeignKey(CommitteeMeeting, related_name="attendance", on_delete=models.CASCADE)
    member = models.ForeignKey(QACommitteeMember, related_name="meeting_attendance", on_delete=models.CASCADE)
    attendance_status = models.CharField(max_length=20, choices=AttendanceStatus.choices)
    remarks = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["meeting", "member"], name="unique_meeting_member_attendance"),
        ]

    def clean(self):
        if self.meeting_id and self.member_id and self.member.committee_id != self.meeting.committee_id:
            raise ValidationError({"member": "Member does not belong to the meeting committee."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class QAAuditCycle(TimeStampedModel):
    class AuditType(models.TextChoices):
        ROUTINE = "routine", "Routine"
        ACCREDITATION_READINESS = "accreditation_readiness", "Accreditation Readiness"
        EXAMINATION_QUALITY = "examination_quality", "Examination Quality"
        CURRICULUM_DELIVERY = "curriculum_delivery", "Curriculum Delivery"
        INFRASTRUCTURE = "infrastructure", "Infrastructure"
        LABORATORY = "laboratory", "Laboratory"
        STUDENT_SUPPORT = "student_support", "Student Support"
        DOCUMENTATION = "documentation", "Documentation"
        RESEARCH = "research", "Research"
        GENERAL = "general", "General"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ONGOING = "ongoing", "Ongoing"
        SUBMITTED = "submitted", "Submitted"
        REVIEWED = "reviewed", "Reviewed"
        CLOSED = "closed", "Closed"

    committee = models.ForeignKey(QACommittee, related_name="audit_cycles", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    audit_type = models.CharField(max_length=40, choices=AuditType.choices, default=AuditType.GENERAL)
    target_faculty = models.ForeignKey("core.Faculty", null=True, blank=True, related_name="qa_audit_cycles", on_delete=models.PROTECT)
    target_department = models.ForeignKey("core.Department", null=True, blank=True, related_name="qa_audit_cycles", on_delete=models.PROTECT)
    target_programme = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="created_qa_audit_cycles", on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-review_period_start"]

    def clean(self):
        if self.review_period_end < self.review_period_start:
            raise ValidationError({"review_period_end": "Review period end cannot be before start."})
        if self.target_department_id and self.target_faculty_id and self.target_department.faculty_id != self.target_faculty_id:
            raise ValidationError({"target_department": "Target department must belong to target faculty."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class QAAuditFinding(TimeStampedModel):
    class SourceModule(models.TextChoices):
        COURSES = "courses", "Courses"
        LECTURES = "lectures", "Lectures"
        EXAMINATIONS = "examinations", "Examinations"
        ACCREDITATION = "accreditation", "Accreditation"
        DOCUMENTS = "documents", "Documents"
        STUDENTS = "students", "Students"
        ANALYTICS = "analytics", "Analytics"
        CORE = "core", "Core"
        MANUAL = "manual", "Manual"

    class Category(models.TextChoices):
        STAFFING = "staffing", "Staffing"
        CURRICULUM = "curriculum", "Curriculum"
        EXAMINATION = "examination", "Examination"
        INFRASTRUCTURE = "infrastructure", "Infrastructure"
        LABORATORY = "laboratory", "Laboratory"
        LIBRARY = "library", "Library"
        RESEARCH = "research", "Research"
        STUDENT_SUPPORT = "student_support", "Student Support"
        DOCUMENTATION = "documentation", "Documentation"
        GOVERNANCE = "governance", "Governance"
        OTHER = "other", "Other"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        UNDER_REVIEW = "under_review", "Under Review"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    audit_cycle = models.ForeignKey(QAAuditCycle, related_name="findings", on_delete=models.CASCADE)
    finding_code = models.CharField(max_length=40, unique=True, blank=True)
    source_module = models.CharField(max_length=40, choices=SourceModule.choices, default=SourceModule.MANUAL)
    source_record_type = models.CharField(max_length=120, blank=True)
    source_record_id = models.CharField(max_length=80, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=40, choices=Category.choices, default=Category.OTHER)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.MODERATE)
    evidence_summary = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="created_qa_findings", on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.finding_code:
            self.finding_code = f"QAF-{self.id:05d}"
            super().save(update_fields=["finding_code"])


class QARecommendation(TimeStampedModel):
    class ResponsibleUnitType(models.TextChoices):
        DEPARTMENT = "department", "Department"
        FACULTY = "faculty", "Faculty"
        PROGRAMME = "programme", "Programme"
        DIRECTORATE = "directorate", "Directorate"
        REGISTRY = "registry", "Registry"
        BURSARY = "bursary", "Bursary"
        LIBRARY = "library", "Library"
        WORKS = "works", "Works"
        STUDENT_AFFAIRS = "student_affairs", "Student Affairs"
        OTHER = "other", "Other"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        IN_PROGRESS = "in_progress", "In Progress"
        IMPLEMENTED = "implemented", "Implemented"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        OVERDUE = "overdue", "Overdue"

    finding = models.ForeignKey(QAAuditFinding, null=True, blank=True, related_name="recommendations", on_delete=models.SET_NULL)
    audit_cycle = models.ForeignKey(QAAuditCycle, related_name="recommendations", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    recommendation_text = models.TextField()
    responsible_unit_type = models.CharField(max_length=40, choices=ResponsibleUnitType.choices)
    responsible_faculty = models.ForeignKey("core.Faculty", null=True, blank=True, related_name="qa_recommendations", on_delete=models.PROTECT)
    responsible_department = models.ForeignKey("core.Department", null=True, blank=True, related_name="qa_recommendations", on_delete=models.PROTECT)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="assigned_qa_recommendations", on_delete=models.SET_NULL)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="created_qa_recommendations", on_delete=models.SET_NULL)

    class Meta:
        ordering = ["due_date", "-created_at"]

    def clean(self):
        if self.responsible_department_id and self.responsible_faculty_id and self.responsible_department.faculty_id != self.responsible_faculty_id:
            raise ValidationError({"responsible_department": "Responsible department must belong to responsible faculty."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class QAActionPlan(TimeStampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    recommendation = models.ForeignKey(QARecommendation, related_name="action_plans", on_delete=models.CASCADE)
    action_description = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="owned_qa_action_plans", on_delete=models.SET_NULL)
    expected_completion_date = models.DateField()
    actual_completion_date = models.DateField(null=True, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    implementation_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["expected_completion_date", "-created_at"]


class QAActionEvidence(TimeStampedModel):
    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    action_plan = models.ForeignKey(QAActionPlan, related_name="evidence", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="qa_committee/evidence/", null=True, blank=True)
    external_url = models.URLField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="uploaded_qa_evidence", on_delete=models.SET_NULL)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="verified_qa_evidence", on_delete=models.SET_NULL)
    verification_status = models.CharField(max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING)
    verification_comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if not self.file and not self.external_url:
            raise ValidationError({"external_url": "Either file or external_url must be provided."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class QACommitteeReport(TimeStampedModel):
    class ReportType(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        ANNUAL = "annual", "Annual"
        ACCREDITATION_READINESS = "accreditation_readiness", "Accreditation Readiness"
        SPECIAL = "special", "Special"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        REVIEWED = "reviewed", "Reviewed"
        APPROVED = "approved", "Approved"

    committee = models.ForeignKey(QACommittee, related_name="reports", on_delete=models.CASCADE)
    audit_cycle = models.ForeignKey(QAAuditCycle, null=True, blank=True, related_name="reports", on_delete=models.SET_NULL)
    report_type = models.CharField(max_length=40, choices=ReportType.choices)
    reporting_period_start = models.DateField()
    reporting_period_end = models.DateField()
    summary = models.TextField()
    key_findings = models.TextField(blank=True)
    recommendations_summary = models.TextField(blank=True)
    action_plan_summary = models.TextField(blank=True)
    qacei_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="submitted_qa_reports", on_delete=models.SET_NULL)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="reviewed_qa_reports", on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-reporting_period_start"]

    def clean(self):
        if self.reporting_period_end < self.reporting_period_start:
            raise ValidationError({"reporting_period_end": "Reporting period end cannot be before start."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class QACommitteeDataReview(TimeStampedModel):
    class ValidationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VALID = "valid", "Valid"
        QUESTIONABLE = "questionable", "Questionable"
        INVALID = "invalid", "Invalid"

    committee = models.ForeignKey(QACommittee, related_name="data_reviews", on_delete=models.CASCADE)
    review_title = models.CharField(max_length=255)
    source_module = models.CharField(max_length=80)
    source_endpoint_or_model = models.CharField(max_length=180, blank=True)
    target_faculty = models.ForeignKey("core.Faculty", null=True, blank=True, related_name="qa_data_reviews", on_delete=models.PROTECT)
    target_department = models.ForeignKey("core.Department", null=True, blank=True, related_name="qa_data_reviews", on_delete=models.PROTECT)
    target_programme = models.CharField(max_length=160, blank=True)
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    extracted_summary = models.JSONField(default=dict, blank=True)
    validation_status = models.CharField(max_length=20, choices=ValidationStatus.choices, default=ValidationStatus.PENDING)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="qa_data_reviews", on_delete=models.SET_NULL)
    reviewer_comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.review_period_end < self.review_period_start:
            raise ValidationError({"review_period_end": "Review period end cannot be before start."})
        if self.target_department_id and self.target_faculty_id and self.target_department.faculty_id != self.target_faculty_id:
            raise ValidationError({"target_department": "Target department must belong to target faculty."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
