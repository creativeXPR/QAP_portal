from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import (
    AccreditationComponent,
    AccreditationCycle,
    AccreditationMetric,
    ComponentScore,
    CorrectiveAction,
    EarlyWarningAlert,
    Evidence,
    MetricSubmission,
    PARIResult,
    RiskClassification,
)
from .services import ensure_default_components_and_metrics


class AccreditationCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccreditationCycle
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class AccreditationComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccreditationComponent
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class AccreditationMetricSerializer(serializers.ModelSerializer):
    component_code = serializers.CharField(source="component.code", read_only=True)

    class Meta:
        model = AccreditationMetric
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "component_code"]


class MetricSubmissionSerializer(serializers.ModelSerializer):
    metric_code = serializers.CharField(source="metric.code", read_only=True)
    component_code = serializers.CharField(source="component.code", read_only=True)

    class Meta:
        model = MetricSubmission
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "submitted_by", "metric_code", "component_code"]

    def validate(self, attrs):
        metric = attrs.get("metric") or getattr(self.instance, "metric", None)
        component = attrs.get("component") or getattr(self.instance, "component", None)
        if metric and component and metric.component_id != component.id:
            raise serializers.ValidationError({"metric": ["Metric does not belong to selected component."]})
        numeric_value = attrs.get("numeric_value")
        if numeric_value is not None and numeric_value < 0:
            raise serializers.ValidationError({"numeric_value": ["Numeric values must not be negative."]})
        return attrs


class BulkMetricResponseSerializer(serializers.Serializer):
    metric = serializers.CharField()
    submitted_value = serializers.CharField(required=False, allow_blank=True)
    numeric_value = serializers.DecimalField(max_digits=14, decimal_places=4, required=False, allow_null=True)
    text_value = serializers.CharField(required=False, allow_blank=True)
    date_value = serializers.DateField(required=False, allow_null=True)
    boolean_value = serializers.BooleanField(required=False, allow_null=True)
    evidence_files = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)

    def validate_numeric_value(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Numeric values must not be negative.")
        return value


class BulkSubmissionSerializer(serializers.Serializer):
    cycle = serializers.PrimaryKeyRelatedField(queryset=AccreditationCycle.objects.all())
    programme = serializers.CharField()
    component = serializers.CharField()
    source_unit = serializers.CharField(required=False, allow_blank=True)
    reporting_period = serializers.CharField()
    responses = BulkMetricResponseSerializer(many=True)

    def validate_component(self, value):
        ensure_default_components_and_metrics()
        try:
            return AccreditationComponent.objects.get(code=value)
        except AccreditationComponent.DoesNotExist as exc:
            raise serializers.ValidationError("Component does not exist.") from exc

    def validate(self, attrs):
        component = attrs["component"]
        for response in attrs["responses"]:
            has_value = any(
                key in response and response.get(key) not in (None, "")
                for key in ("submitted_value", "numeric_value", "text_value", "date_value", "boolean_value")
            )
            if not has_value:
                raise serializers.ValidationError({"responses": ["Each response must include at least one metric value."]})
            metric_code = response["metric"]
            if not AccreditationMetric.objects.filter(component=component, code=metric_code, is_active=True).exists():
                raise serializers.ValidationError({"metric": [f"{metric_code} does not belong to selected component."]})
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        user = self.context["request"].user
        cycle = self.validated_data["cycle"]
        programme = str(self.validated_data["programme"])
        component = self.validated_data["component"]
        reporting_period = self.validated_data["reporting_period"]
        source_unit = self.validated_data.get("source_unit", "")
        submissions = []
        for response in self.validated_data["responses"]:
            metric = AccreditationMetric.objects.get(component=component, code=response["metric"])
            defaults = {
                "submitted_value": response.get("submitted_value", ""),
                "numeric_value": response.get("numeric_value"),
                "text_value": response.get("text_value", ""),
                "date_value": response.get("date_value"),
                "boolean_value": response.get("boolean_value"),
                "source_unit": source_unit,
                "submitted_by": user,
                "validation_status": "pending",
            }
            submission, _ = MetricSubmission.objects.update_or_create(
                cycle=cycle,
                programme=programme,
                component=component,
                metric=metric,
                reporting_period=reporting_period,
                defaults=defaults,
            )
            for file_obj in response.get("evidence_files", []):
                Evidence.objects.create(
                    cycle=cycle,
                    programme=programme,
                    component=component,
                    metric=metric,
                    submission=submission,
                    title=file_obj.name,
                    evidence_type="submission",
                    file=file_obj,
                    uploaded_by=user,
                )
            submissions.append(submission)
        return submissions


class EvidenceSerializer(serializers.ModelSerializer):
    component_code = serializers.CharField(source="component.code", read_only=True)
    metric_code = serializers.CharField(source="metric.code", read_only=True)

    class Meta:
        model = Evidence
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "uploaded_by", "upload_date", "component_code", "metric_code"]

    def validate(self, attrs):
        component = attrs.get("component") or getattr(self.instance, "component", None)
        metric = attrs.get("metric") or getattr(self.instance, "metric", None)
        submission = attrs.get("submission") or getattr(self.instance, "submission", None)
        if metric and component and metric.component_id != component.id:
            raise serializers.ValidationError({"metric": ["Metric does not belong to selected component."]})
        if submission and component and submission.component_id != component.id:
            raise serializers.ValidationError({"submission": ["Submission does not belong to selected component."]})
        return attrs


class ComponentScoreSerializer(serializers.ModelSerializer):
    component_code = serializers.CharField(source="component.code", read_only=True)

    class Meta:
        model = ComponentScore
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "component_code"]


class PARIResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PARIResult
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class RiskClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskClassification
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class EarlyWarningAlertSerializer(serializers.ModelSerializer):
    component_code = serializers.CharField(source="component.code", read_only=True)

    class Meta:
        model = EarlyWarningAlert
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "resolved_at", "component_code"]


class CorrectiveActionSerializer(serializers.ModelSerializer):
    component_code = serializers.CharField(source="component.code", read_only=True)

    class Meta:
        model = CorrectiveAction
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "verified_by", "verified_at", "component_code"]

    def validate_progress_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Progress must be between 0 and 100.")
        return value


class CorrectiveActionProgressSerializer(serializers.Serializer):
    progress_percentage = serializers.IntegerField(min_value=0, max_value=100)
    reviewer_comment = serializers.CharField(required=False, allow_blank=True)


class ReviewerCommentSerializer(serializers.Serializer):
    reviewer_comment = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def apply_evidence_status(self, evidence, status):
        evidence.verification_status = status
        evidence.reviewer_comment = self.validated_data.get("reviewer_comment", "")
        if status == "rejected":
            evidence.rejection_reason = self.validated_data.get("rejection_reason", "")
        evidence.save()
        return evidence

    def apply_action_status(self, action, status, user=None):
        comment = self.validated_data.get("reviewer_comment", "")
        if status == "verified":
            action.verified_by = user
            action.verified_at = timezone.now()
        action.status = status
        if comment:
            action.reviewer_comment = comment
        action.save()
        return action
