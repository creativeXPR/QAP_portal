from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]


class ExamSession(models.Model):
    department = models.ForeignKey(
        "core.Department", on_delete=models.CASCADE, related_name="exam_sessions"
    )
    course_code_title = models.CharField(max_length=255)  # free text, e.g. "AGM 410"
    exam_date = models.DateField()
    venue = models.CharField(max_length=255)
    academic_session = models.CharField(max_length=40)  # e.g. "First Semester 2025/2026"

    class Meta:
        ordering = ["-exam_date"]

    def __str__(self):
        return f"{self.course_code_title} @ {self.venue} ({self.exam_date})"


class ExamQualityReport(models.Model):
    exam_session = models.ForeignKey(
        ExamSession, on_delete=models.CASCADE, related_name="quality_reports"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="exam_quality_reports_submitted"
    )

    # Examination Environment Quality
    adequacy_of_seating = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    lighting_conditions = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    ventilation_room_comfort = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    noise_free_environment = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    accessibility_suitability_of_venue = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)

    # Invigilation Quality
    invigilators_arrived_on_time = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    clear_communication_of_instructions = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    professional_conduct_of_invigilators = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    fair_consistent_enforcement_of_rules = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    responsiveness_to_student_needs = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)

    # Examination Administration Processes
    prompt_start_of_examination = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    organized_distribution_of_materials = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    proper_management_of_exam_time = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    orderliness_during_submission = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    provision_for_special_needs = models.PositiveSmallIntegerField(
        validators=RATING_VALIDATORS, null=True, blank=True
    )  # "if applicable" on the form — not required

    # Misconduct and Incident Reporting
    observed_misconduct = models.BooleanField()
    incident_description = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)

    # Overall Evaluation
    overall_rating = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    suggestions_for_improvement = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Exam quality report for {self.exam_session} — {self.submitted_at:%Y-%m-%d}"