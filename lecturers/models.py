from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]


class LecturerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lecturer_profile"
    )
    department = models.ForeignKey(
        "core.Department", on_delete=models.CASCADE, related_name="lecturers"
    )
    staff_id = models.CharField(max_length=30, unique=True)
    rank = models.CharField(max_length=100, blank=True)  # e.g. "Senior Lecturer", "Professor"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.department.name})"

class AssessmentReport(models.Model):
    INDICATOR_FIELDS = [
        "presents_content_actively",
        "covers_content_within_timeframe",
        "gives_useful_assignments",
        "impressive_comportment",
        "punctual_at_lectures",
        "available_for_consultation",
        "clear_on_concepts",
        "links_theory_to_practice",
        "encourages_participation",
        "provides_assignment_feedback",
        "teaches_per_course_outline",
        "teaches_class_regularly",
        "updates_course_content",
        "uses_real_life_examples",
        "appears_neatly",
        "uses_varied_teaching_methods",
        "uses_technology_innovatively",
    ]

    lecturer = models.ForeignKey(
        LecturerProfile, on_delete=models.CASCADE, related_name="assessment_reports"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="lecturer_assessments_submitted"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.PROTECT, related_name="lecturer_assessments"
    )
    academic_session = models.CharField(max_length=20)  # e.g. "2025/2026"
    semester = models.CharField(max_length=20, blank=True)
    presents_content_actively = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    covers_content_within_timeframe = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    gives_useful_assignments = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    impressive_comportment = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    punctual_at_lectures = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    available_for_consultation = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    clear_on_concepts = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    links_theory_to_practice = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    encourages_participation = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    provides_assignment_feedback = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    teaches_per_course_outline = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    teaches_class_regularly = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    updates_course_content = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    uses_real_life_examples = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    appears_neatly = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    uses_varied_teaching_methods = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    uses_technology_innovatively = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)

    included_in_dossier = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        values = [getattr(self, f) for f in self.INDICATOR_FIELDS]
        return round(sum(values) / len(values), 2)

    def __str__(self):
        return f"Assessment of {self.lecturer} — {self.academic_session}"