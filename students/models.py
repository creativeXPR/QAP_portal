from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class Student(models.Model):
    class Level(models.TextChoices):
        L100 = "100", "100 Level"
        L200 = "200", "200 Level"
        L300 = "300", "300 Level"
        L400 = "400", "400 Level"
        L500 = "500", "500 Level"
        PG = "PG", "Postgraduate"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        SUSPENDED = "suspended", "Suspended"
        GRADUATED = "graduated", "Graduated"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="student_record",
        on_delete=models.SET_NULL,
    )
    faculty = models.ForeignKey("core.Faculty", related_name="students", on_delete=models.PROTECT)
    department = models.ForeignKey("core.Department", related_name="students", on_delete=models.PROTECT)
    courses = models.ManyToManyField("courses.Course", blank=True, related_name="enrolled_students")
    matric_number = models.CharField(
        max_length=40,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9/_-]+$",
                message="Matric number may contain only letters, numbers, slash, underscore, and hyphen.",
            )
        ],
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    programme = models.CharField(max_length=160)
    level = models.CharField(max_length=10, choices=Level.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["matric_number"]

    def clean(self):
        if self.department_id and self.faculty_id and self.department.faculty_id != self.faculty_id:
            raise ValidationError({"department": "Department must belong to the selected faculty."})

    def save(self, *args, **kwargs):
        self.matric_number = self.matric_number.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.matric_number} - {self.first_name} {self.last_name}"


class StudentFeedback(models.Model):
    class Category(models.TextChoices):
        COMPLAINT = "complaint", "Complaint"
        SUGGESTION = "suggestion", "Suggestion"
        INQUIRY = "inquiry", "Inquiry"
        ACADEMIC = "academic", "Academic"
        SUPPORT = "support", "Support"
        OTHER = "other", "Other"

    class Classification(models.TextChoices):
        ACADEMIC = "academic", "Academic"
        ADMINISTRATIVE = "administrative", "Administrative"
        FACILITY = "facility", "Facility"
        WELFARE = "welfare", "Welfare"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under Review"
        # IN_PROGRESS = "in_progress", "In Progress"
        # AWAITING_STUDENT_RESPONSE = "awaiting_student_response", "Awaiting Student Response"
        RESOLVED = "resolved", "Resolved"
        # CLOSED = "closed", "Closed"
        # REJECTED = "rejected", "Rejected"

    class Urgency(models.TextChoices):
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class SubmissionMode(models.TextChoices):
        Anonymous = "anonymous", "Anonymous"
        CONFIDENTIAL = "confidential", "Confidential"
        OPEN_IDENTITY = "open_identity", "Open_Identity"

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="student_feedback",
        on_delete=models.SET_NULL,
    )
    student_name = models.CharField(max_length=100)
    student_email = models.EmailField(default="", blank=True, null=True)
    feedback_text = models.TextField()
    category = models.CharField(max_length=50)
    classification = models.CharField(max_length=50, default=Classification.ACADEMIC)
    status = models.CharField(max_length=30, default=Status.PENDING)
    urgency = models.CharField(max_length=20, default=Urgency.NORMAL)
    submission_mode = models.CharField(max_length=50, default=SubmissionMode.OPEN_IDENTITY, blank=True)
    admin_comment = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="assigned_student_feedback",
        on_delete=models.SET_NULL,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="updated_student_feedback",
        on_delete=models.SET_NULL,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Feedback from {self.student_name} at {self.submitted_at}"


class StudentFeedbackAttachment(models.Model):
    complaint = models.ForeignKey(StudentFeedback, related_name="attachments", on_delete=models.CASCADE)
    file = models.FileField(upload_to="student_feedback/attachments/")
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="student_feedback_attachments",
        on_delete=models.SET_NULL,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at", "id"]

    def __str__(self):
        return self.original_name


class StudentFeedbackUpdate(models.Model):
    complaint = models.ForeignKey(StudentFeedback, related_name="updates", on_delete=models.CASCADE)
    previous_status = models.CharField(max_length=30, choices=StudentFeedback.Status.choices, blank=True)
    new_status = models.CharField(max_length=30, choices=StudentFeedback.Status.choices)
    admin_comment = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="student_feedback_assignment_updates",
        on_delete=models.SET_NULL,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="student_feedback_updates",
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.complaint_id}: {self.previous_status} -> {self.new_status}"


class StudentNotification(models.Model):
    class NotificationType(models.TextChoices):
        COMPLAINT_UPDATE = "complaint_update", "Complaint Update"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="student_notifications", on_delete=models.CASCADE)
    complaint = models.ForeignKey(
        StudentFeedback,
        null=True,
        blank=True,
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=160)
    message = models.TextField()
    notification_type = models.CharField(max_length=40, choices=NotificationType.choices, default=NotificationType.COMPLAINT_UPDATE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} for {self.user}"
