from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Course(models.Model):
    department = models.ForeignKey(
        "core.Department", on_delete=models.CASCADE, related_name="courses"
    )
    code = models.CharField(max_length=20, unique=True)  # e.g. STA 101
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title}"


class LectureSession(models.Model):
    class TimeSlot(models.TextChoices):
        SLOT_08_09 = "08:00-09:00", "8:00 – 9:00"
        SLOT_09_10 = "09:00-10:00", "9:00 – 10:00"
        SLOT_10_11 = "10:00-11:00", "10:00 – 11:00"
        SLOT_11_12 = "11:00-12:00", "11:00 – 12:00"
        SLOT_12_13 = "12:00-13:00", "12:00 – 1:00"
        SLOT_13_14 = "13:00-14:00", "1:00 – 2:00"
        SLOT_14_15 = "14:00-15:00", "2:00 – 3:00"
        SLOT_15_16 = "15:00-16:00", "3:00 – 4:00"
        SLOT_16_17 = "16:00-17:00", "4:00 – 5:00"
        SLOT_17_18 = "17:00-18:00", "5:00 – 6:00"
        SLOT_18_19 = "18:00-19:00", "6:00 – 7:00"

    class Level(models.TextChoices):
        L100 = "100", "100 Level"
        L200 = "200", "200 Level"
        L300 = "300", "300 Level"
        L400 = "400", "400 Level"
        L500 = "500", "500 Level"
        PG = "PG", "Postgraduate"

    class Mode(models.TextChoices):
        PHYSICAL = "physical", "Physical Classroom"
        ONLINE = "online", "Online (LMS/Zoom/Meet)"
        HYBRID = "hybrid", "Hybrid"

    class LecturerPresence(models.TextChoices):
        YES = "yes", "Yes"
        LATE = "late", "Late"
        NO = "no", "No"

    class Duration(models.TextChoices):
        UNDER_30 = "<30", "Less than 30 minutes"
        MIN_30_45 = "30-45", "30 – 45 minutes"
        MIN_45_60 = "45-60", "45 – 60 minutes"
        OVER_60 = ">60", "More than 60 minutes"

    class ReasonNotHeld(models.TextChoices):
        LECTURER_ABSENT = "lecturer_absent", "Lecturer absent"
        STUDENTS_ABSENT = "students_absent", "Students absent"
        VENUE_UNAVAILABLE = "venue_unavailable", "Venue not available"
        HOLIDAY_STRIKE = "holiday_strike", "Public holiday / strike"
        TIMETABLE_CLASH = "timetable_clash", "Time Table clash"
        TECHNICAL = "technical", "Technical issues"
        OTHER = "other", "Other"

    class Attendance(models.TextChoices):
        UNDER_100 = "<100", "Less than 100"
        RANGE_100_500 = "100-500", "100 - 500"
        RANGE_500_1000 = "500-1000", "500 - 1000"
        OVER_1000 = ">1000", "More than 1000"

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lecture_sessions"
    )
    respondent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lecture_monitoring_reports",
    )
    monitored_at = models.DateTimeField()
    time_slot = models.CharField(max_length=20, choices=TimeSlot.choices)
    level = models.CharField(max_length=10, choices=Level.choices)
    mode = models.CharField(max_length=10, choices=Mode.choices)

    lecturer_present = models.CharField(max_length=10, choices=LecturerPresence.choices)
    actual_duration = models.CharField(max_length=10, choices=Duration.choices)
    venue = models.CharField(max_length=255)

    held = models.BooleanField()
    explanation = models.TextField(blank=True)
    reason_not_held = models.CharField(
        max_length=30, choices=ReasonNotHeld.choices, blank=True
    )

    estimated_attendance = models.CharField(max_length=10, choices=Attendance.choices)
    classroom_environment_rating = models.PositiveSmallIntegerField()
    teaching_effectiveness_rating = models.PositiveSmallIntegerField()
    quality_concerns = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-monitored_at"]

    def clean(self):
        errors = {}

        if not self.held and not self.reason_not_held:
            errors["reason_not_held"] = "Required when the lecture did not hold."

        if self.held and self.reason_not_held:
            errors["reason_not_held"] = "Should be blank when the lecture held."

        for field in ("classroom_environment_rating", "teaching_effectiveness_rating"):
            value = getattr(self, field)
            if value is not None and not (1 <= value <= 5):
                errors[field] = "Rating must be between 1 and 5."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.code} @ {self.monitored_at:%Y-%m-%d %H:%M}"