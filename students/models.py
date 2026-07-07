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
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"

    class Urgency(models.TextChoices):
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

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
    category = models.CharField(max_length=50, choices=Category.choices)
    classification = models.CharField(max_length=50, choices=Classification.choices, default=Classification.ACADEMIC)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    urgency = models.CharField(max_length=20, choices=Urgency.choices, default=Urgency.NORMAL)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Feedback from {self.student_name} at {self.submitted_at}"
