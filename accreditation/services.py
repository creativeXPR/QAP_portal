from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime

from django.db import transaction
from django.db.models import Avg
from django.utils import timezone

from analytics.services import calculate_formula

from .constants import DEFAULT_COMPONENTS, DEFAULT_METRICS, PARI_COMPONENT_CODES
from .models import (
    AccreditationComponent,
    AccreditationMetric,
    ComponentScore,
    EarlyWarningAlert,
    MetricSubmission,
    PARIResult,
    RiskClassification,
)


def quantize(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def ensure_default_components_and_metrics():
    for component_data in DEFAULT_COMPONENTS:
        component, _ = AccreditationComponent.objects.update_or_create(
            code=component_data["code"],
            defaults=component_data,
        )
        for code, name, value_type, formula_key, benchmark, required_evidence in DEFAULT_METRICS.get(component.code, []):
            AccreditationMetric.objects.update_or_create(
                component=component,
                code=code,
                defaults={
                    "name": name,
                    "value_type": value_type,
                    "formula_key": formula_key,
                    "minimum_benchmark": benchmark,
                    "required_evidence": required_evidence,
                    "is_active": True,
                },
            )


def classify_score(score):
    if score is None:
        return "no_data"
    if score >= 80:
        return "good"
    if score >= 60:
        return "warning"
    return "critical"


def classify_pari(score):
    if score >= 80:
        return "accreditation_ready"
    if score >= 60:
        return "moderate_risk"
    return "high_risk"


def _submitted_values(cycle, programme, component):
    submissions = MetricSubmission.objects.filter(cycle=cycle, programme=str(programme), component=component)
    values = {}
    for submission in submissions.select_related("metric"):
        metric = submission.metric
        if submission.numeric_value is not None:
            values[metric.code] = float(submission.numeric_value)
        elif submission.date_value is not None:
            values[metric.code] = submission.date_value
        elif submission.boolean_value is not None:
            values[metric.code] = submission.boolean_value
        elif submission.text_value:
            values[metric.code] = submission.text_value
        elif submission.submitted_value:
            values[metric.code] = submission.submitted_value
    return values


def _json_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _normalise_metric_score(metric, value):
    if value is None:
        return None
    value = float(value)
    if metric.formula_key in {"staff_to_student_ratio"}:
        target = float(metric.minimum_benchmark or 20)
        if value <= target:
            return 100.0
        return max(0.0, 100.0 - ((value - target) * 5.0))
    if metric.formula_key in {"malpractice_rate", "result_release_turnaround_time", "average_complaint_resolution_time"}:
        target = float(metric.minimum_benchmark or 1)
        if value <= target:
            return 100.0
        return max(0.0, 100.0 - ((value - target) / target * 100.0))
    if metric.formula_key == "qacei":
        return max(0.0, min((value / 5.0) * 100.0, 100.0))
    if metric.minimum_benchmark:
        benchmark = float(metric.minimum_benchmark)
        if benchmark == 0:
            return None
        return max(0.0, min((value / benchmark) * 100.0, 100.0))
    return max(0.0, min(value, 100.0))


@transaction.atomic
def calculate_component_scores(cycle, programme, user=None):
    ensure_default_components_and_metrics()
    programme = str(programme)
    results = []
    for component in AccreditationComponent.objects.filter(is_active=True).prefetch_related("metrics"):
        values = _submitted_values(cycle, programme, component)
        metric_breakdown = {}
        metric_scores = []
        for metric in component.metrics.filter(is_active=True):
            if metric.formula_key:
                value = calculate_formula(metric.formula_key, values)
                if value is not None:
                    metric_breakdown[metric.code] = value
                    score = _normalise_metric_score(metric, value)
                    if score is not None:
                        metric_scores.append(score)
            elif metric.code in values:
                metric_breakdown[metric.code] = _json_value(values[metric.code])
        score = None if not metric_scores else sum(metric_scores) / len(metric_scores)
        stored_score = quantize(score or 0)
        status = classify_score(score)
        component_score, _ = ComponentScore.objects.update_or_create(
            cycle=cycle,
            programme=programme,
            component=component,
            defaults={
                "score": stored_score,
                "status": status,
                "metrics": metric_breakdown,
                "calculated_by": user if getattr(user, "is_authenticated", False) else None,
                "calculated_at": timezone.now(),
            },
        )
        results.append(
            {
                "component": component.code,
                "score": float(component_score.score),
                "status": component_score.status,
                "metrics": metric_breakdown,
            }
        )
    return results


def _alert_for_pari(cycle, programme, classification, pari_score):
    if classification == "accreditation_ready":
        return None, False
    severity = "critical" if classification == "high_risk" else "high"
    lookup = {
        "cycle": cycle,
        "programme": str(programme),
        "trigger_type": f"pari_{classification}",
    }
    alert = EarlyWarningAlert.objects.filter(**lookup, status__in=["open", "acknowledged", "in_progress", "escalated"]).first()
    if alert:
        alert.severity = severity
        alert.message = f"PARI score is {pari_score:.2f}; programme is classified as {classification.replace('_', ' ')}."
        alert.status = "open"
        alert.save(update_fields=["severity", "message", "status", "updated_at"])
        return alert, False
    alert = EarlyWarningAlert.objects.create(
        cycle=cycle,
        programme=str(programme),
        trigger_type=f"pari_{classification}",
        severity=severity,
        message=f"PARI score is {pari_score:.2f}; programme is classified as {classification.replace('_', ' ')}.",
        status="open",
    )
    return alert, True


def _component_alert_trigger(component_code):
    return {
        "staffing": "staffing_shortage",
        "curriculum_delivery": "low_lecture_delivery",
        "infrastructure": "poor_infrastructure",
        "research": "weak_research_output",
        "student_outcomes": "student_dissatisfaction",
        "laboratory_facilities": "lab_functionality_below_80",
        "library_resources": "library_resource_gaps",
        "qa_compliance": "poor_qa_committee_performance",
        "examination_quality": "delayed_result_release",
        "student_support": "high_complaint_rate",
    }.get(component_code, "component_risk")


def create_component_alerts(cycle, programme):
    created_count = 0
    weak_scores = ComponentScore.objects.filter(cycle=cycle, programme=str(programme), status__in=["warning", "critical"])
    for score in weak_scores.select_related("component"):
        severity = "critical" if score.status == "critical" else "medium"
        _, created = EarlyWarningAlert.objects.get_or_create(
            cycle=cycle,
            programme=str(programme),
            component=score.component,
            trigger_type=_component_alert_trigger(score.component.code),
            status="open",
            defaults={
                "severity": severity,
                "message": f"{score.component.name} score is {float(score.score):.2f}, requiring attention.",
            },
        )
        created_count += int(created)
    return created_count


@transaction.atomic
def calculate_pari(cycle, programme, user=None):
    ensure_default_components_and_metrics()
    programme = str(programme)
    calculate_component_scores(cycle, programme, user=user)
    scores = {
        score.component.code: score
        for score in ComponentScore.objects.filter(cycle=cycle, programme=programme, component__code__in=PARI_COMPONENT_CODES).select_related(
            "component"
        )
    }
    breakdown = []
    pari_score = Decimal("0.00")
    for code in PARI_COMPONENT_CODES:
        component = AccreditationComponent.objects.get(code=code)
        score = scores.get(code)
        raw_score = Decimal(score.score if score else 0)
        weight = Decimal(component.weight)
        weighted_score = (weight / Decimal("100.00")) * raw_score
        pari_score += weighted_score
        breakdown.append(
            {
                "component": code,
                "weight": float(weight),
                "score": float(raw_score),
                "weighted_score": float(quantize(weighted_score)),
            }
        )
    pari_score = quantize(pari_score)
    classification = classify_pari(float(pari_score))
    result, _ = PARIResult.objects.update_or_create(
        cycle=cycle,
        programme=programme,
        defaults={
            "pari_score": pari_score,
            "classification": classification,
            "breakdown": breakdown,
            "calculated_by": user if getattr(user, "is_authenticated", False) else None,
            "calculated_at": timezone.now(),
        },
    )
    RiskClassification.objects.update_or_create(
        cycle=cycle,
        programme=programme,
        defaults={"classification": classification, "pari_score": pari_score},
    )
    _, pari_alert_created = _alert_for_pari(cycle, programme, classification, float(pari_score))
    alerts_created = int(pari_alert_created) + create_component_alerts(cycle, programme)
    return {
        "programme": programme,
        "cycle": cycle.id,
        "pari_score": float(result.pari_score),
        "classification": result.classification,
        "breakdown": breakdown,
        "alerts_created": alerts_created,
    }


def evidence_completion_rate():
    required_metrics = AccreditationMetric.objects.filter(required_evidence=True).count()
    if required_metrics == 0:
        return 0
    verified = AccreditationMetric.objects.filter(required_evidence=True, evidence__verification_status="verified").distinct().count()
    return round((verified / required_metrics) * 100, 2)


def average_component_scores():
    return ComponentScore.objects.values("component__code", "component__name").annotate(average_score=Avg("score"))
