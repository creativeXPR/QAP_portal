from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .constants import (
    ACTION_PRIORITIES,
    ACTION_STATUSES,
    ALERT_SEVERITIES,
    ALERT_STATUSES,
    CYCLE_STATUSES,
    EVIDENCE_STATUSES,
    RISK_CLASSIFICATIONS,
    SCORE_STATUSES,
    VALIDATION_STATUSES,
    VALUE_TYPES,
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AccreditationCycle(TimeStampedModel):
    title = models.CharField(max_length=255)
    academic_session = models.CharField(max_length=32)
    semester = models.CharField(max_length=32, blank=True)
    accreditation_body = models.CharField(max_length=120, blank=True)
    accreditation_type = models.CharField(max_length=120, blank=True)
    faculty = models.CharField(max_length=160, blank=True)
    department = models.CharField(max_length=160, blank=True)
    programme = models.CharField(max_length=160, blank=True)
    start_date = models.DateField()
    submission_deadline = models.DateField(null=True, blank=True)
    internal_review_deadline = models.DateField(null=True, blank=True)
    external_visit_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=40, choices=CYCLE_STATUSES, default="draft")

    class Meta:
        ordering = ["-start_date", "title"]

    def __str__(self):
        return f"{self.title} ({self.academic_session})"

    def close(self):
        self.status = "closed"
        self.save(update_fields=["status", "updated_at"])


class AccreditationComponent(TimeStampedModel):
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    collection_frequency = models.CharField(max_length=80, blank=True)
    information_suppliers = models.TextField(blank=True)
    collection_method = models.TextField(blank=True)
    dashboard_output = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name


class AccreditationMetric(TimeStampedModel):
    component = models.ForeignKey(AccreditationComponent, related_name="metrics", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    value_type = models.CharField(max_length=20, choices=VALUE_TYPES, default="numeric")
    unit = models.CharField(max_length=50, blank=True)
    formula_key = models.SlugField(max_length=100, null=True, blank=True)
    minimum_benchmark = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    warning_threshold = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    danger_threshold = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    required_evidence = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["component__code", "code"]
        constraints = [
            models.UniqueConstraint(fields=["component", "code"], name="unique_accreditation_metric_code"),
        ]

    def __str__(self):
        return f"{self.component.code}: {self.code}"


class MetricSubmission(TimeStampedModel):
    cycle = models.ForeignKey(AccreditationCycle, related_name="submissions", on_delete=models.CASCADE)
    programme = models.CharField(max_length=160)
    component = models.ForeignKey(AccreditationComponent, related_name="submissions", on_delete=models.CASCADE)
    metric = models.ForeignKey(AccreditationMetric, related_name="submissions", on_delete=models.CASCADE)
    submitted_value = models.TextField(blank=True)
    numeric_value = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    text_value = models.TextField(blank=True)
    date_value = models.DateField(null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    source_unit = models.CharField(max_length=160, blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reporting_period = models.CharField(max_length=50)
    validation_status = models.CharField(max_length=30, choices=VALIDATION_STATUSES, default="pending")
    reviewer_comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cycle", "programme", "component", "metric", "reporting_period"],
                name="unique_metric_submission_period",
            ),
        ]

    def __str__(self):
        return f"{self.programme} {self.cycle_id} {self.metric.code}"

    def clean(self):
        if self.metric_id and self.component_id and self.metric.component_id != self.component_id:
            from django.core.exceptions import ValidationError

            raise ValidationError({"metric": "Metric does not belong to selected component."})


class Evidence(TimeStampedModel):
    cycle = models.ForeignKey(AccreditationCycle, related_name="evidence", on_delete=models.CASCADE)
    programme = models.CharField(max_length=160)
    component = models.ForeignKey(AccreditationComponent, related_name="evidence", on_delete=models.CASCADE)
    metric = models.ForeignKey(AccreditationMetric, null=True, blank=True, related_name="evidence", on_delete=models.SET_NULL)
    submission = models.ForeignKey(MetricSubmission, null=True, blank=True, related_name="evidence", on_delete=models.SET_NULL)
    corrective_action = models.ForeignKey(
        "CorrectiveAction", null=True, blank=True, related_name="evidence", on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=255)
    evidence_type = models.CharField(max_length=80, blank=True)
    file = models.FileField(upload_to="accreditation/evidence/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    upload_date = models.DateTimeField(default=timezone.now)
    verification_status = models.CharField(max_length=30, choices=EVIDENCE_STATUSES, default="uploaded")
    reviewer_comment = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-upload_date"]

    def __str__(self):
        return self.title


class ComponentScore(TimeStampedModel):
    cycle = models.ForeignKey(AccreditationCycle, related_name="component_scores", on_delete=models.CASCADE)
    programme = models.CharField(max_length=160)
    component = models.ForeignKey(AccreditationComponent, related_name="scores", on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=SCORE_STATUSES, default="no_data")
    metrics = models.JSONField(default=dict, blank=True)
    calculated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    calculated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["component__code"]
        constraints = [
            models.UniqueConstraint(fields=["cycle", "programme", "component"], name="unique_component_score"),
        ]

    def __str__(self):
        return f"{self.programme} {self.component.code}: {self.score}"


class PARIResult(TimeStampedModel):
    cycle = models.ForeignKey(AccreditationCycle, related_name="pari_results", on_delete=models.CASCADE)
    programme = models.CharField(max_length=160)
    pari_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    classification = models.CharField(max_length=40, choices=RISK_CLASSIFICATIONS)
    breakdown = models.JSONField(default=list, blank=True)
    calculated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    calculated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-calculated_at"]
        constraints = [
            models.UniqueConstraint(fields=["cycle", "programme"], name="unique_pari_result"),
        ]

    def __str__(self):
        return f"{self.programme}: {self.pari_score}"


class RiskClassification(TimeStampedModel):
    cycle = models.ForeignKey(AccreditationCycle, related_name="risk_classifications", on_delete=models.CASCADE)
    programme = models.CharField(max_length=160)
    classification = models.CharField(max_length=40, choices=RISK_CLASSIFICATIONS)
    pari_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["classification", "programme"]
        constraints = [
            models.UniqueConstraint(fields=["cycle", "programme"], name="unique_risk_classification"),
        ]

    def __str__(self):
        return f"{self.programme}: {self.classification}"


class EarlyWarningAlert(TimeStampedModel):
    cycle = models.ForeignKey(AccreditationCycle, related_name="alerts", on_delete=models.CASCADE)
    programme = models.CharField(max_length=160)
    component = models.ForeignKey(AccreditationComponent, null=True, blank=True, related_name="alerts", on_delete=models.SET_NULL)
    trigger_type = models.CharField(max_length=80)
    severity = models.CharField(max_length=20, choices=ALERT_SEVERITIES, default="medium")
    message = models.TextField()
    status = models.CharField(max_length=20, choices=ALERT_STATUSES, default="open")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["cycle", "programme", "status"]),
            models.Index(fields=["trigger_type", "severity"]),
        ]

    def __str__(self):
        return f"{self.programme}: {self.trigger_type}"


class CorrectiveAction(TimeStampedModel):
    cycle = models.ForeignKey(AccreditationCycle, related_name="corrective_actions", on_delete=models.CASCADE)
    programme = models.CharField(max_length=160)
    component = models.ForeignKey(
        AccreditationComponent, null=True, blank=True, related_name="corrective_actions", on_delete=models.SET_NULL
    )
    alert = models.ForeignKey(EarlyWarningAlert, null=True, blank=True, related_name="corrective_actions", on_delete=models.SET_NULL)
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_unit = models.CharField(max_length=160, blank=True)
    responsible_officer = models.CharField(max_length=160, blank=True)
    priority = models.CharField(max_length=20, choices=ACTION_PRIORITIES, default="medium")
    deadline = models.DateField(null=True, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    status = models.CharField(max_length=40, choices=ACTION_STATUSES, default="open")
    completion_evidence = models.FileField(upload_to="accreditation/actions/", null=True, blank=True)
    reviewer_comment = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="verified_actions", on_delete=models.SET_NULL)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["deadline", "-created_at"]

    def __str__(self):
        return self.title

    def set_status(self, status, user=None, comment=""):
        self.status = status
        if comment:
            self.reviewer_comment = comment
        if status == "verified":
            self.verified_by = user
            self.verified_at = timezone.now()
        self.save()
