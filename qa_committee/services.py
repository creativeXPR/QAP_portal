from collections import Counter

from django.apps import apps
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import (
    CommitteeMeeting,
    QAActionEvidence,
    QAActionPlan,
    QAAuditFinding,
    QACommittee,
    QACommitteeDataReview,
    QACommitteeReport,
    QARecommendation,
)


def safe_model_import(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except (LookupError, ValueError):
        return None


def percentage(numerator, denominator):
    denominator = denominator or 0
    if denominator == 0:
        return 0
    return round((float(numerator or 0) / float(denominator)) * 100, 2)


def get_committee_effectiveness_score(committee, start_date=None, end_date=None):
    score = 0
    max_score = 5
    if committee:
        score += 1
    meetings = committee.meetings.all()
    reports = committee.reports.all()
    findings = QAAuditFinding.objects.filter(audit_cycle__committee=committee)
    action_plans = QAActionPlan.objects.filter(recommendation__audit_cycle__committee=committee)
    if start_date:
        meetings = meetings.filter(scheduled_date__date__gte=start_date)
        reports = reports.filter(reporting_period_end__gte=start_date)
        findings = findings.filter(created_at__date__gte=start_date)
        action_plans = action_plans.filter(created_at__date__gte=start_date)
    if end_date:
        meetings = meetings.filter(scheduled_date__date__lte=end_date)
        reports = reports.filter(reporting_period_start__lte=end_date)
        findings = findings.filter(created_at__date__lte=end_date)
        action_plans = action_plans.filter(created_at__date__lte=end_date)
    if meetings.filter(status="held").exists():
        score += 1
    if reports.filter(status__in=["submitted", "reviewed", "approved"]).exists():
        score += 1
    if findings.exists():
        score += 1
    if action_plans.exists():
        score += 1
    return round((score / max_score) * 5, 2)


def get_overdue_recommendations(faculty=None, department=None):
    queryset = QARecommendation.objects.filter(due_date__lt=timezone.localdate()).exclude(status__in=["implemented", "verified", "rejected"])
    if faculty:
        queryset = queryset.filter(Q(responsible_faculty=faculty) | Q(audit_cycle__target_faculty=faculty))
    if department:
        queryset = queryset.filter(Q(responsible_department=department) | Q(audit_cycle__target_department=department))
    return queryset


def get_open_findings(faculty=None, department=None):
    queryset = QAAuditFinding.objects.exclude(status__in=["resolved", "dismissed"])
    if faculty:
        queryset = queryset.filter(audit_cycle__target_faculty=faculty)
    if department:
        queryset = queryset.filter(audit_cycle__target_department=department)
    return queryset


def get_action_plan_completion_rate(faculty=None, department=None):
    queryset = QAActionPlan.objects.select_related("recommendation__audit_cycle")
    if faculty:
        queryset = queryset.filter(recommendation__audit_cycle__target_faculty=faculty)
    if department:
        queryset = queryset.filter(recommendation__audit_cycle__target_department=department)
    return percentage(queryset.filter(status__in=["completed", "verified"]).count(), queryset.count())


def get_committee_activity_summary(start_date=None, end_date=None):
    meetings = CommitteeMeeting.objects.all()
    reports = QACommitteeReport.objects.all()
    findings = QAAuditFinding.objects.all()
    recommendations = QARecommendation.objects.all()
    if start_date:
        meetings = meetings.filter(created_at__date__gte=start_date)
        reports = reports.filter(created_at__date__gte=start_date)
        findings = findings.filter(created_at__date__gte=start_date)
        recommendations = recommendations.filter(created_at__date__gte=start_date)
    if end_date:
        meetings = meetings.filter(created_at__date__lte=end_date)
        reports = reports.filter(created_at__date__lte=end_date)
        findings = findings.filter(created_at__date__lte=end_date)
        recommendations = recommendations.filter(created_at__date__lte=end_date)
    return {
        "meetings": meetings.count(),
        "reports": reports.count(),
        "findings": findings.count(),
        "recommendations": recommendations.count(),
    }


def get_risk_summary_by_department():
    return list(
        QAAuditFinding.objects.values("audit_cycle__target_department__name")
        .annotate(total=Count("id"), critical=Count("id", filter=Q(severity="critical")))
        .order_by("-critical", "-total")
    )


def get_risk_summary_by_faculty():
    return list(
        QAAuditFinding.objects.values("audit_cycle__target_faculty__name")
        .annotate(total=Count("id"), critical=Count("id", filter=Q(severity="critical")))
        .order_by("-critical", "-total")
    )


def summarize_external_module(source_module, faculty=None, department=None, start_date=None, end_date=None):
    if source_module in {"courses", "lectures"}:
        LectureSession = safe_model_import("courses", "LectureSession")
        if not LectureSession:
            return {"module": source_module, "status": "module_not_available", "data": {}}
        queryset = LectureSession.objects.select_related("course__department__faculty")
        if faculty:
            queryset = queryset.filter(course__department__faculty=faculty)
        if department:
            queryset = queryset.filter(course__department=department)
        if start_date:
            queryset = queryset.filter(monitored_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(monitored_at__date__lte=end_date)
        total = queryset.count()
        held = queryset.filter(held=True).count()
        return {"module": source_module, "status": "available", "data": {"scheduled_lectures": total, "held_lectures": held, "lecture_delivery_rate": percentage(held, total)}}
    if source_module == "examinations":
        ExamQualityReport = safe_model_import("examinations", "ExamQualityReport")
        if not ExamQualityReport:
            return {"module": source_module, "status": "module_not_available", "data": {}}
        queryset = ExamQualityReport.objects.select_related("exam_session__department__faculty")
        if faculty:
            queryset = queryset.filter(exam_session__department__faculty=faculty)
        if department:
            queryset = queryset.filter(exam_session__department=department)
        return {"module": source_module, "status": "available", "data": {"quality_reports": queryset.count(), "malpractice_cases": queryset.filter(observed_misconduct=True).count(), "average_quality_score": queryset.aggregate(value=Avg("overall_rating"))["value"] or 0}}
    if source_module == "accreditation":
        PARIResult = safe_model_import("accreditation", "PARIResult")
        if not PARIResult:
            return {"module": source_module, "status": "module_not_available", "data": {}}
        queryset = PARIResult.objects.select_related("cycle")
        return {"module": source_module, "status": "available", "data": {"programmes": queryset.values("programme").distinct().count(), "average_pari": queryset.aggregate(value=Avg("pari_score"))["value"] or 0}}
    if source_module == "documents":
        Document = safe_model_import("documents", "InstitutionalDocument")
        if not Document:
            return {"module": source_module, "status": "module_not_available", "data": {}}
        queryset = Document.objects.all()
        return {"module": source_module, "status": "available", "data": {"documents": queryset.count(), "pending_review": queryset.filter(status="pending_review").count(), "published": queryset.filter(status="published").count()}}
    if source_module == "students":
        Feedback = safe_model_import("students", "StudentFeedback")
        if not Feedback:
            return {"module": source_module, "status": "module_not_available", "data": {}}
        queryset = Feedback.objects.all()
        return {"module": source_module, "status": "available", "data": {"feedback": queryset.count(), "pending": queryset.filter(status="pending").count(), "resolved": queryset.filter(status="resolved").count()}}
    return {"module": source_module, "status": "module_not_available", "data": {}}


def get_committee_summary(filters=None):
    filters = filters or {}
    committees = QACommittee.objects.all()
    if filters.get("faculty"):
        committees = committees.filter(faculty=filters["faculty"])
    if filters.get("department"):
        committees = committees.filter(department=filters["department"])
    findings = QAAuditFinding.objects.all()
    recommendations = QARecommendation.objects.all()
    action_plans = QAActionPlan.objects.all()
    evidence = QAActionEvidence.objects.all()
    qacei_scores = [get_committee_effectiveness_score(committee) for committee in committees]
    return {
        "total_committees": committees.count(),
        "active_committees": committees.filter(status="active").count(),
        "meetings_held_this_quarter": CommitteeMeeting.objects.filter(status="held").count(),
        "open_findings": findings.exclude(status__in=["resolved", "dismissed"]).count(),
        "critical_findings": findings.filter(severity="critical").exclude(status__in=["resolved", "dismissed"]).count(),
        "recommendations_pending": recommendations.filter(status="pending").count(),
        "recommendations_overdue": get_overdue_recommendations().count(),
        "action_plans_completed": action_plans.filter(status__in=["completed", "verified"]).count(),
        "evidence_pending_verification": evidence.filter(verification_status="pending").count(),
        "average_qacei_score": round(sum(qacei_scores) / len(qacei_scores), 2) if qacei_scores else 0,
        "departments_at_qa_risk": get_risk_summary_by_department(),
        "faculties_with_unresolved_recommendations": list(recommendations.exclude(status__in=["implemented", "verified", "rejected"]).values("responsible_faculty__name").annotate(count=Count("id"))),
    }


def get_committee_dashboard(committee):
    return {
        "committee": {"id": committee.id, "name": committee.name, "status": committee.status},
        "qacei_score": get_committee_effectiveness_score(committee),
        "meetings": committee.meetings.count(),
        "members": committee.members.filter(is_active=True).count(),
        "findings": QAAuditFinding.objects.filter(audit_cycle__committee=committee).count(),
        "recommendations": QARecommendation.objects.filter(audit_cycle__committee=committee).count(),
        "open_action_plans": QAActionPlan.objects.filter(recommendation__audit_cycle__committee=committee).exclude(status__in=["completed", "verified"]).count(),
    }


def get_activity_feed(limit=20):
    items = []
    for finding in QAAuditFinding.objects.select_related("created_by").order_by("-created_at")[:limit]:
        items.append(_activity(f"finding-{finding.id}", "qa_finding_created", finding.title, finding.description, finding.severity, finding.created_at, finding.created_by))
    for recommendation in QARecommendation.objects.select_related("created_by").order_by("-created_at")[:limit]:
        items.append(_activity(f"recommendation-{recommendation.id}", "qa_recommendation_created", recommendation.title, recommendation.recommendation_text, recommendation.priority, recommendation.created_at, recommendation.created_by))
    for report in QACommitteeReport.objects.select_related("submitted_by").exclude(submitted_at__isnull=True).order_by("-submitted_at")[:limit]:
        items.append(_activity(f"report-{report.id}", "qa_report_submitted", report.get_report_type_display(), report.summary, report.status, report.submitted_at, report.submitted_by))
    return sorted(items, key=lambda item: item["created_at"], reverse=True)[:limit]


def _activity(item_id, activity_type, title, description, severity, created_at, actor):
    return {
        "id": str(item_id),
        "type": activity_type,
        "title": title,
        "description": description,
        "module": "qa_committee",
        "severity": severity,
        "created_at": created_at,
        "actor": {
            "id": getattr(actor, "id", None),
            "name": getattr(actor, "get_full_name", lambda: "")() or getattr(actor, "username", ""),
        } if actor else None,
    }
