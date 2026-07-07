from collections import Counter
from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.db.models import Avg, Count, Q
from django.utils import timezone


READINESS_LABELS = ["accreditation_ready", "moderate_risk", "high_risk"]
SEVERITY_LABELS = ["low", "medium", "high", "critical"]


def safe_model_import(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except (LookupError, ValueError):
        return None


def module_available(app_label):
    return apps.is_installed(app_label)


def percentage(numerator, denominator):
    try:
        denominator = float(denominator or 0)
        if denominator == 0:
            return 0
        return round((float(numerator or 0) / denominator) * 100, 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


def number(value):
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return float(value)
    return value


def status_from_score(score):
    score = float(score or 0)
    if score >= 80:
        return "good"
    if score >= 60:
        return "moderate_risk"
    return "high_risk"


def build_chart(chart_type, labels, data, label):
    return {
        "type": chart_type,
        "labels": list(labels),
        "datasets": [{"label": label, "data": [number(item) for item in data]}],
    }


def empty_module_response(module_name, message=None):
    return {
        "module": module_name,
        "status": "module_not_available",
        "message": message or f"{module_name} module is not available.",
        "data": [],
    }


def _has_field(model, field_name):
    if model is None:
        return False
    return any(field.name == field_name for field in model._meta.get_fields())


def _today():
    return timezone.localdate()


def resolve_date_range(request):
    today = _today()
    period = request.query_params.get("period")
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")

    if start_date or end_date:
        return start_date, end_date
    if period == "this_week":
        return today - timedelta(days=today.weekday()), today
    if period == "this_month":
        return today.replace(day=1), today
    if period == "this_quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=quarter_start_month, day=1), today
    if period == "this_year":
        return today.replace(month=1, day=1), today
    return None, None


def parse_dashboard_filters(request):
    start_date, end_date = resolve_date_range(request)
    limit = request.query_params.get("limit", 20)
    try:
        limit = min(max(int(limit), 1), 100)
    except (TypeError, ValueError):
        limit = 20
    return {
        "faculty_id": request.query_params.get("faculty_id"),
        "department_id": request.query_params.get("department_id"),
        "programme_id": request.query_params.get("programme_id"),
        "committee_id": request.query_params.get("committee_id"),
        "start_date": start_date,
        "end_date": end_date,
        "status": request.query_params.get("status"),
        "risk_level": request.query_params.get("risk_level"),
        "severity": request.query_params.get("severity"),
        "limit": limit,
    }


def _apply_date_filters(queryset, filters, field_name):
    if queryset is None or not field_name:
        return queryset
    model = queryset.model
    if not _has_field(model, field_name):
        return queryset
    if filters.get("start_date"):
        queryset = queryset.filter(**{f"{field_name}__date__gte" if "DateTime" in model._meta.get_field(field_name).__class__.__name__ else f"{field_name}__gte": filters["start_date"]})
    if filters.get("end_date"):
        queryset = queryset.filter(**{f"{field_name}__date__lte" if "DateTime" in model._meta.get_field(field_name).__class__.__name__ else f"{field_name}__lte": filters["end_date"]})
    return queryset


def apply_faculty_department_filters(queryset, filters):
    if queryset is None:
        return queryset
    model = queryset.model
    faculty_id = filters.get("faculty_id")
    department_id = filters.get("department_id")
    if faculty_id:
        if _has_field(model, "faculty"):
            queryset = queryset.filter(faculty_id=faculty_id)
        elif _has_field(model, "department"):
            queryset = queryset.filter(department__faculty_id=faculty_id)
        elif _has_field(model, "cycle"):
            Faculty = safe_model_import("core", "Faculty")
            faculty = Faculty.objects.filter(pk=faculty_id).first() if Faculty else None
            if faculty:
                queryset = queryset.filter(cycle__faculty=faculty.name)
    if department_id:
        if _has_field(model, "department"):
            queryset = queryset.filter(department_id=department_id)
        elif _has_field(model, "cycle"):
            Department = safe_model_import("core", "Department")
            department = Department.objects.filter(pk=department_id).first() if Department else None
            if department:
                queryset = queryset.filter(cycle__department=department.name)
    return queryset


def _count(model, filters=None, date_field=None):
    if model is None:
        return 0
    queryset = model.objects.all()
    if filters:
        queryset = apply_faculty_department_filters(queryset, filters)
        queryset = _apply_date_filters(queryset, filters, date_field)
    return queryset.count()


def _avg(queryset, field_name):
    if queryset is None:
        return 0
    return round(float(queryset.aggregate(value=Avg(field_name))["value"] or 0), 2)


def _list_values(queryset, *fields, limit=20):
    if queryset is None:
        return []
    return list(queryset.values(*fields)[:limit])


def _pari_queryset(filters):
    PARIResult = safe_model_import("accreditation", "PARIResult")
    if PARIResult is None:
        return None
    queryset = PARIResult.objects.select_related("cycle").all()
    queryset = apply_faculty_department_filters(queryset, filters)
    queryset = _apply_date_filters(queryset, filters, "calculated_at")
    if filters.get("programme_id"):
        queryset = queryset.filter(programme=filters["programme_id"])
    if filters.get("risk_level"):
        queryset = queryset.filter(classification=filters["risk_level"])
    return queryset


def _component_score_queryset(filters):
    ComponentScore = safe_model_import("accreditation", "ComponentScore")
    if ComponentScore is None:
        return None
    queryset = ComponentScore.objects.select_related("cycle", "component").all()
    queryset = apply_faculty_department_filters(queryset, filters)
    return _apply_date_filters(queryset, filters, "calculated_at")


def _alert_queryset(filters):
    EarlyWarningAlert = safe_model_import("accreditation", "EarlyWarningAlert")
    if EarlyWarningAlert is None:
        return None
    queryset = EarlyWarningAlert.objects.select_related("cycle", "component").all()
    queryset = apply_faculty_department_filters(queryset, filters)
    queryset = _apply_date_filters(queryset, filters, "created_at")
    if filters.get("severity"):
        queryset = queryset.filter(severity=filters["severity"])
    return queryset


def _programme_count(filters):
    pari = _pari_queryset(filters)
    if pari is not None and pari.exists():
        return pari.values("programme").distinct().count()
    Student = safe_model_import("students", "Student")
    if Student is None:
        return 0
    queryset = apply_faculty_department_filters(Student.objects.all(), filters)
    return queryset.values("programme").distinct().count()


def _qa_committee_unavailable():
    return empty_module_response(
        "qa_committee",
        "QA committee data is not available because the qa_committee module has no installed data models.",
    )


def _qa_committee_metrics():
    QACommittee = safe_model_import("qa_committee", "QACommittee")
    if QACommittee is None:
        return None
    from qa_committee.services import get_committee_effectiveness_score

    committees = QACommittee.objects.all()
    qacei_scores = [get_committee_effectiveness_score(committee) for committee in committees]
    return {
        "committees": committees,
        "active_count": committees.filter(status="active").count(),
        "average_qacei_score": round(sum(qacei_scores) / len(qacei_scores), 2) if qacei_scores else 0,
    }


def get_university_overview(filters):
    Faculty = safe_model_import("core", "Faculty")
    Department = safe_model_import("core", "Department")
    Evidence = safe_model_import("accreditation", "Evidence")
    CorrectiveAction = safe_model_import("accreditation", "CorrectiveAction")
    pari = _pari_queryset(filters)
    alerts = _alert_queryset(filters)
    qa_metrics = _qa_committee_metrics()

    pending_evidence = 0
    if Evidence is not None:
        evidence = apply_faculty_department_filters(Evidence.objects.select_related("cycle"), filters)
        pending_evidence = evidence.exclude(verification_status="verified").count()

    overdue_actions = 0
    if CorrectiveAction is not None:
        actions = apply_faculty_department_filters(CorrectiveAction.objects.select_related("cycle"), filters)
        overdue_actions = actions.filter(deadline__lt=_today()).exclude(status__in=["verified", "closed"]).count()

    data = {
        "filters": filters,
        "kpis": {
            "total_faculties": _count(Faculty),
            "total_departments": _count(Department, filters),
            "total_programmes": _programme_count(filters),
            "programmes_accreditation_ready": pari.filter(classification="accreditation_ready").count() if pari is not None else 0,
            "programmes_moderate_risk": pari.filter(classification="moderate_risk").count() if pari is not None else 0,
            "programmes_high_risk": pari.filter(classification="high_risk").count() if pari is not None else 0,
            "average_pari_score": _avg(pari, "pari_score") if pari is not None else 0,
            "active_qa_committees": qa_metrics["active_count"] if qa_metrics else 0,
            "average_qacei_score": qa_metrics["average_qacei_score"] if qa_metrics else 0,
            "open_critical_findings": alerts.filter(severity="critical").exclude(status="resolved").count() if alerts is not None else 0,
            "overdue_recommendations": overdue_actions,
            "pending_evidence_verifications": pending_evidence,
        },
        "recent_accreditation_alerts": _recent_alerts(filters, limit=5),
        "recent_qa_activities": get_activity_feed(filters)[:5],
        "module_status": {
            "core": "available" if Faculty and Department else "module_not_available",
            "accreditation": "available" if pari is not None else "module_not_available",
            "qa_committee": "available" if qa_metrics else "module_not_available",
        },
    }
    return data


def _readiness_distribution(pari):
    return {label: pari.filter(classification=label).count() if pari is not None else 0 for label in READINESS_LABELS}


def get_accreditation_dashboard(filters):
    pari = _pari_queryset(filters)
    scores = _component_score_queryset(filters)
    Evidence = safe_model_import("accreditation", "Evidence")
    if pari is None or scores is None:
        return empty_module_response("accreditation", "Accreditation data is not available.")

    distribution = _readiness_distribution(pari)
    programme_rows = list(pari.values("programme", "pari_score", "classification").order_by("programme"))
    trend_rows = list(pari.values("programme", "pari_score", "classification", "calculated_at").order_by("calculated_at")[:100])
    faculty_rows = list(
        pari.values("cycle__faculty")
        .annotate(average_pari_score=Avg("pari_score"))
        .order_by("cycle__faculty")
    )
    component_rows = list(
        scores.values("component__code", "component__name")
        .annotate(average_score=Avg("score"))
        .order_by("average_score")
    )
    component_items = [
        {
            "component": row["component__code"],
            "name": row["component__name"],
            "average_score": round(float(row["average_score"] or 0), 2),
        }
        for row in component_rows
    ]
    missing_evidence = []
    if Evidence is not None:
        evidence = apply_faculty_department_filters(Evidence.objects.select_related("cycle", "component"), filters)
        missing_evidence = list(
            evidence.exclude(verification_status="verified")
            .values("programme", "title", "verification_status", "component__code")
            .order_by("-upload_date")[:20]
        )

    return {
        "readiness_distribution": distribution,
        "average_readiness_score": _avg(pari, "pari_score"),
        "pari_scores_by_programme": programme_rows,
        "pari_scores_by_faculty": [
            {"faculty": row["cycle__faculty"] or "Unspecified", "average_pari_score": round(float(row["average_pari_score"] or 0), 2)}
            for row in faculty_rows
        ],
        "weakest_accreditation_components": component_items[:5],
        "strongest_accreditation_components": sorted(component_items, key=lambda item: item["average_score"], reverse=True)[:5],
        "programmes_on_watch_list": list(pari.filter(classification="moderate_risk").values("programme", "pari_score")[:20]),
        "programmes_at_risk": list(pari.filter(classification="high_risk").values("programme", "pari_score")[:20]),
        "trend_over_time": trend_rows,
        "missing_accreditation_evidence": missing_evidence,
        "charts": {
            "readiness_distribution_pie": build_chart("pie", distribution.keys(), distribution.values(), "Programmes"),
            "pari_by_programme_bar": build_chart("bar", [row["programme"] for row in programme_rows], [row["pari_score"] for row in programme_rows], "PARI Score"),
            "pari_by_faculty_bar": build_chart(
                "bar",
                [row["cycle__faculty"] or "Unspecified" for row in faculty_rows],
                [row["average_pari_score"] or 0 for row in faculty_rows],
                "Average PARI",
            ),
            "risk_trend_line": build_chart("line", [str(row["calculated_at"]) for row in trend_rows], [row["pari_score"] for row in trend_rows], "PARI"),
            "component_score_radar_or_bar": build_chart(
                "bar",
                [item["component"] for item in component_items],
                [item["average_score"] for item in component_items],
                "Component Score",
            ),
        },
    }


def get_qa_committee_dashboard(filters):
    QACommittee = safe_model_import("qa_committee", "QACommittee")
    if QACommittee is None:
        return {
            "module_status": _qa_committee_unavailable(),
            "total_committees": 0,
            "active_committees": 0,
            "committees_with_meetings_this_quarter": 0,
            "committees_without_recent_meetings": [],
            "reports_submitted": 0,
            "reports_pending": 0,
            "open_findings": 0,
            "critical_findings": 0,
            "recommendations_pending": 0,
            "recommendations_implemented": 0,
            "recommendations_overdue": 0,
            "action_plan_completion_rate": 0,
            "evidence_pending_verification": 0,
            "average_qacei_score": 0,
            "qacei_by_committee": [],
            "qacei_by_faculty_department": [],
            "charts": {
                "qacei_by_committee_bar": build_chart("bar", [], [], "QACEI"),
                "findings_by_severity_pie": build_chart("pie", SEVERITY_LABELS, [0, 0, 0, 0], "Findings"),
                "recommendations_by_status_bar": build_chart("bar", ["pending", "implemented", "overdue"], [0, 0, 0], "Recommendations"),
                "action_plan_completion_trend_line": build_chart("line", [], [], "Completion Rate"),
            },
        }
    from qa_committee.services import get_action_plan_completion_rate, get_committee_effectiveness_score, get_overdue_recommendations

    QAAuditFinding = safe_model_import("qa_committee", "QAAuditFinding")
    QARecommendation = safe_model_import("qa_committee", "QARecommendation")
    QAActionEvidence = safe_model_import("qa_committee", "QAActionEvidence")
    QACommitteeReport = safe_model_import("qa_committee", "QACommitteeReport")
    CommitteeMeeting = safe_model_import("qa_committee", "CommitteeMeeting")
    committees = QACommittee.objects.select_related("faculty", "department").all()
    qacei_rows = [
        {"committee": committee.name, "committee_id": committee.id, "qacei_score": get_committee_effectiveness_score(committee)}
        for committee in committees
    ]
    severity_counts = {label: QAAuditFinding.objects.filter(severity=label).count() if QAAuditFinding else 0 for label in SEVERITY_LABELS}
    recommendation_statuses = ["pending", "implemented", "overdue"]
    recommendation_counts = [
        QARecommendation.objects.filter(status=status_value).count() if QARecommendation else 0
        for status_value in recommendation_statuses
    ]
    average_qacei = round(sum(row["qacei_score"] for row in qacei_rows) / len(qacei_rows), 2) if qacei_rows else 0
    return {
        "module_status": {"module": "qa_committee", "status": "available", "message": "QA committee data is available.", "data": []},
        "total_committees": committees.count(),
        "active_committees": committees.filter(status="active").count(),
        "committees_with_meetings_this_quarter": CommitteeMeeting.objects.filter(status="held").count() if CommitteeMeeting else 0,
        "committees_without_recent_meetings": [],
        "reports_submitted": QACommitteeReport.objects.filter(status__in=["submitted", "reviewed", "approved"]).count() if QACommitteeReport else 0,
        "reports_pending": QACommitteeReport.objects.filter(status="draft").count() if QACommitteeReport else 0,
        "open_findings": QAAuditFinding.objects.exclude(status__in=["resolved", "dismissed"]).count() if QAAuditFinding else 0,
        "critical_findings": QAAuditFinding.objects.filter(severity="critical").exclude(status__in=["resolved", "dismissed"]).count() if QAAuditFinding else 0,
        "recommendations_pending": QARecommendation.objects.filter(status="pending").count() if QARecommendation else 0,
        "recommendations_implemented": QARecommendation.objects.filter(status__in=["implemented", "verified"]).count() if QARecommendation else 0,
        "recommendations_overdue": get_overdue_recommendations().count(),
        "action_plan_completion_rate": get_action_plan_completion_rate(),
        "evidence_pending_verification": QAActionEvidence.objects.filter(verification_status="pending").count() if QAActionEvidence else 0,
        "average_qacei_score": average_qacei,
        "qacei_by_committee": qacei_rows,
        "qacei_by_faculty_department": list(committees.values("faculty__name", "department__name").annotate(committees=Count("id"))),
        "charts": {
            "qacei_by_committee_bar": build_chart("bar", [row["committee"] for row in qacei_rows], [row["qacei_score"] for row in qacei_rows], "QACEI"),
            "findings_by_severity_pie": build_chart("pie", severity_counts.keys(), severity_counts.values(), "Findings"),
            "recommendations_by_status_bar": build_chart("bar", recommendation_statuses, recommendation_counts, "Recommendations"),
            "action_plan_completion_trend_line": build_chart("line", [], [], "Completion Rate"),
        },
    }


def get_teaching_learning_dashboard(filters):
    Course = safe_model_import("courses", "Course")
    LectureSession = safe_model_import("courses", "LectureSession")
    if Course is None and LectureSession is None:
        return empty_module_response("courses", "Teaching and lecture delivery data is not available.")
    courses = apply_faculty_department_filters(Course.objects.select_related("department", "department__faculty"), filters) if Course else None
    lectures = LectureSession.objects.select_related("course", "course__department", "course__department__faculty") if LectureSession else None
    if lectures is not None:
        lectures = apply_faculty_department_filters(lectures, filters)
        lectures = _apply_date_filters(lectures, filters, "monitored_at")
    scheduled = lectures.count() if lectures is not None else 0
    held = lectures.filter(held=True).count() if lectures is not None else 0
    by_department = []
    if lectures is not None:
        by_department = list(
            lectures.values("course__department__name")
            .annotate(scheduled=Count("id"), held=Count("id", filter=Q(held=True)))
            .order_by("course__department__name")
        )
    return {
        "total_courses": courses.count() if courses is not None else 0,
        "courses_with_approved_outlines": 0,
        "courses_uploaded_to_lms": 0,
        "scheduled_lectures": scheduled,
        "lectures_held": held,
        "average_lecture_delivery_rate": percentage(held, scheduled),
        "average_course_coverage_rate": 0,
        "courses_fully_delivered": 0,
        "courses_partially_delivered": 0,
        "courses_at_risk": [],
        "low_performing_departments": [
            {"department": row["course__department__name"], "delivery_rate": percentage(row["held"], row["scheduled"])}
            for row in by_department
            if percentage(row["held"], row["scheduled"]) < 60
        ],
        "lecturer_punctuality": percentage(lectures.filter(lecturer_present="yes").count(), scheduled) if lectures is not None else 0,
        "charts": {
            "lecture_delivery_by_department_bar": build_chart(
                "bar",
                [row["course__department__name"] or "Unspecified" for row in by_department],
                [percentage(row["held"], row["scheduled"]) for row in by_department],
                "Lecture Delivery Rate",
            ),
            "course_coverage_by_course_bar": build_chart("bar", [], [], "Course Coverage"),
            "courses_by_delivery_status_pie": build_chart("pie", ["fully_delivered", "partially_delivered", "at_risk"], [0, 0, 0], "Courses"),
            "monthly_lecture_delivery_trend_line": build_chart("line", [], [], "Lecture Delivery"),
        },
    }


def get_examination_dashboard(filters):
    ExamSession = safe_model_import("examinations", "ExamSession")
    ExamQualityReport = safe_model_import("examinations", "ExamQualityReport")
    if ExamSession is None or ExamQualityReport is None:
        return empty_module_response("examinations", "Examination quality data is not available.")
    sessions = apply_faculty_department_filters(ExamSession.objects.select_related("department", "department__faculty"), filters)
    sessions = _apply_date_filters(sessions, filters, "exam_date")
    reports = ExamQualityReport.objects.select_related("exam_session", "exam_session__department", "exam_session__department__faculty")
    reports = apply_faculty_department_filters(reports, filters)
    reports = _apply_date_filters(reports, filters, "submitted_at")
    environment_fields = ["adequacy_of_seating", "lighting_conditions", "ventilation_room_comfort", "noise_free_environment", "accessibility_suitability_of_venue"]
    invigilation_fields = ["invigilators_arrived_on_time", "clear_communication_of_instructions", "professional_conduct_of_invigilators", "fair_consistent_enforcement_of_rules", "responsiveness_to_student_needs"]
    administration_fields = ["prompt_start_of_examination", "organized_distribution_of_materials", "proper_management_of_exam_time", "orderliness_during_submission"]
    return {
        "total_exam_sessions": sessions.count(),
        "exam_quality_reports_submitted": reports.count(),
        "average_examination_administration_score": _average_fields(reports, administration_fields),
        "average_invigilation_score": _average_fields(reports, invigilation_fields),
        "average_environment_score": _average_fields(reports, environment_fields),
        "overall_examination_quality_score": _avg(reports, "overall_rating"),
        "malpractice_cases": reports.filter(observed_misconduct=True).count(),
        "malpractice_rate": percentage(reports.filter(observed_misconduct=True).count(), reports.count()) * 10,
        "result_release_average_turnaround_time": 0,
        "external_examiner_compliance_rate": 0,
        "unresolved_exam_issues": list(reports.filter(observed_misconduct=True).values("exam_session__course_code_title", "incident_description", "submitted_at")[:20]),
        "charts": {
            "exam_quality_score_trend_line": build_chart("line", [str(row["submitted_at"]) for row in reports.values("submitted_at")[:50]], [row["overall_rating"] for row in reports.values("overall_rating")[:50]], "Overall Rating"),
            "malpractice_by_faculty_bar": _malpractice_by_faculty_chart(reports),
            "result_release_turnaround_bar": build_chart("bar", [], [], "Turnaround Days"),
            "exam_issues_by_status_pie": build_chart("pie", ["reported", "resolved"], [reports.filter(observed_misconduct=True).count(), 0], "Exam Issues"),
        },
    }


def _average_fields(queryset, fields):
    if queryset is None or not queryset.exists():
        return 0
    values = []
    for field in fields:
        values.append(queryset.aggregate(value=Avg(field))["value"] or 0)
    return round(sum(float(value) for value in values) / len(values), 2) if values else 0


def _malpractice_by_faculty_chart(reports):
    rows = reports.filter(observed_misconduct=True).values("exam_session__department__faculty__name").annotate(count=Count("id"))
    return build_chart("bar", [row["exam_session__department__faculty__name"] or "Unspecified" for row in rows], [row["count"] for row in rows], "Malpractice Cases")


def get_documents_dashboard(filters):
    Document = safe_model_import("documents", "InstitutionalDocument")
    Category = safe_model_import("documents", "InstitutionalDocumentCategory")
    if Document is None:
        return empty_module_response("documents", "Institutional document data is not available.")
    documents = Document.objects.select_related("category").all()
    documents = _apply_date_filters(documents, filters, "created_at")
    by_category = list(documents.values("category__name").annotate(count=Count("id")).order_by("category__name"))
    by_status = list(documents.values("status").annotate(count=Count("id")).order_by("status"))
    total_required = Category.objects.filter(is_active=True).count() if Category else 0
    submitted = documents.count()
    return {
        "total_documents": submitted,
        "documents_by_category": by_category,
        "required_documents": total_required,
        "submitted_documents": submitted,
        "missing_documents": max(total_required - documents.values("category").distinct().count(), 0),
        "pending_review_documents": documents.filter(status="pending_review").count(),
        "approved_documents": documents.filter(status="approved").count(),
        "rejected_documents": documents.filter(status="rejected").count(),
        "documents_expiring_soon": list(documents.filter(expiry_date__isnull=False, expiry_date__lte=_today() + timedelta(days=60)).values("title", "expiry_date", "status")[:20]),
        "document_completeness_percentage": percentage(documents.values("category").distinct().count(), total_required),
        "charts": {
            "documents_by_category_bar": build_chart("bar", [row["category__name"] or "Uncategorized" for row in by_category], [row["count"] for row in by_category], "Documents"),
            "document_status_pie": build_chart("pie", [row["status"] for row in by_status], [row["count"] for row in by_status], "Documents"),
            "document_completeness_by_department_bar": build_chart("bar", [], [], "Completeness"),
            "expiring_documents_timeline": build_chart("line", [], [], "Expiring Documents"),
        },
    }


def get_student_experience_dashboard(filters):
    Feedback = safe_model_import("students", "StudentFeedback")
    if Feedback is None:
        return empty_module_response("students", "Student feedback data is not available.")
    feedback = Feedback.objects.select_related("submitted_by").all()
    feedback = _apply_date_filters(feedback, filters, "submitted_at")
    total = feedback.count()
    resolved = feedback.filter(status="resolved").count()
    pending = feedback.filter(status="pending").count()
    by_status = list(feedback.values("status").annotate(count=Count("id")).order_by("status"))
    by_category = list(feedback.values("category").annotate(count=Count("id")).order_by("category"))
    return {
        "total_feedback_responses": total,
        "average_student_satisfaction_score": 0,
        "teaching_effectiveness_score": 0,
        "academic_advising_satisfaction": 0,
        "total_complaints": feedback.filter(category="complaint").count(),
        "resolved_complaints": resolved,
        "pending_complaints": pending,
        "complaint_resolution_rate": percentage(resolved, total),
        "average_complaint_resolution_time": 0,
        "counselling_usage": 0,
        "disability_support_provision": 0,
        "charts": {
            "satisfaction_trend_line": build_chart("line", [], [], "Satisfaction"),
            "complaints_by_status_pie": build_chart("pie", [row["status"] for row in by_status], [row["count"] for row in by_status], "Feedback"),
            "complaints_by_category_bar": build_chart("bar", [row["category"] for row in by_category], [row["count"] for row in by_category], "Feedback"),
            "resolution_time_by_department_bar": build_chart("bar", [], [], "Resolution Time"),
        },
    }


def get_infrastructure_labs_dashboard(filters):
    scores = _component_score_queryset(filters)
    if scores is None:
        return empty_module_response("accreditation", "Infrastructure and laboratory metrics are not available.")
    infrastructure = scores.filter(component__code__in=["infrastructure", "laboratory_facilities"])
    avg_score = _avg(infrastructure, "score")
    lab_score = _avg(scores.filter(component__code="laboratory_facilities"), "score")
    return {
        "classroom_adequacy_score": _avg(scores.filter(component__code="infrastructure"), "score"),
        "seating_capacity_utilization": 0,
        "electricity_availability_score": avg_score,
        "internet_uptime": 0,
        "ventilation_score": 0,
        "accessibility_compliance": 0,
        "number_of_laboratories": 0,
        "functional_laboratories": 0,
        "equipment_functionality_rate": lab_score,
        "laboratory_utilization_rate": 0,
        "practical_to_theory_ratio": 0,
        "labs_by_status": {"green": 1 if lab_score >= 80 else 0, "yellow": 1 if 60 <= lab_score < 80 else 0, "red": 1 if lab_score < 60 and lab_score else 0},
        "charts": {
            "infrastructure_quality_by_department_bar": build_chart("bar", [], [], "Infrastructure Quality"),
            "lab_functionality_status_pie": build_chart("pie", ["green", "yellow", "red"], [1 if lab_score >= 80 else 0, 1 if 60 <= lab_score < 80 else 0, 1 if lab_score < 60 and lab_score else 0], "Labs"),
            "equipment_functionality_by_lab_bar": build_chart("bar", [], [], "Equipment Functionality"),
            "infrastructure_risk_heatmap": {"type": "heatmap", "labels": [], "datasets": []},
        },
    }


def get_research_dashboard(filters):
    scores = _component_score_queryset(filters)
    if scores is None:
        return empty_module_response("accreditation", "Research metrics are not available.")
    research_scores = scores.filter(component__code="research_innovation")
    return {
        "publications_per_academic_staff": 0,
        "total_publications": 0,
        "grant_income": 0,
        "conference_participation": 0,
        "postgraduate_supervision_completion_rate": 0,
        "research_productivity_index": _avg(research_scores, "score"),
        "top_departments_by_research_output": [],
        "departments_with_weak_research_output": [],
        "charts": {
            "publications_by_department_bar": build_chart("bar", [], [], "Publications"),
            "grant_income_by_faculty_bar": build_chart("bar", [], [], "Grant Income"),
            "research_productivity_trend_line": build_chart("line", [str(row["calculated_at"]) for row in research_scores.values("calculated_at")[:50]], [row["score"] for row in research_scores.values("score")[:50]], "Research Score"),
            "postgraduate_completion_rate_bar": build_chart("bar", [], [], "Completion Rate"),
        },
    }


def get_early_warning_dashboard(filters):
    pari = _pari_queryset(filters)
    alerts = _alert_queryset(filters)
    if pari is None or alerts is None:
        return empty_module_response("accreditation", "Early warning data is not available.")
    distribution = _readiness_distribution(pari)
    severity = {label: alerts.filter(severity=label).count() for label in SEVERITY_LABELS}
    drivers = Counter(alerts.values_list("trigger_type", flat=True))
    return {
        "accreditation_secure_count": distribution["accreditation_ready"],
        "accreditation_watch_list_count": distribution["moderate_risk"],
        "accreditation_risk_count": distribution["high_risk"],
        "high_risk_programmes": list(pari.filter(classification="high_risk").values("programme", "pari_score")[:20]),
        "high_risk_departments": list(pari.filter(classification="high_risk").values("cycle__department").annotate(count=Count("id")).order_by("-count")[:20]),
        "risk_drivers": [{"driver": key, "count": value} for key, value in drivers.items()],
        "recent_alerts": _recent_alerts(filters, limit=20),
        "alert_severity_distribution": severity,
        "recommended_actions": _recommended_actions(filters),
        "charts": {
            "risk_category_distribution_pie": build_chart("pie", distribution.keys(), distribution.values(), "Programmes"),
            "risk_by_faculty_bar": _risk_by_faculty_chart(pari),
            "risk_driver_frequency_bar": build_chart("bar", drivers.keys(), drivers.values(), "Drivers"),
            "risk_trend_line": build_chart("line", [str(row["calculated_at"]) for row in pari.values("calculated_at")[:50]], [row["pari_score"] for row in pari.values("pari_score")[:50]], "PARI"),
        },
    }


def _risk_by_faculty_chart(pari):
    rows = pari.filter(classification="high_risk").values("cycle__faculty").annotate(count=Count("id"))
    return build_chart("bar", [row["cycle__faculty"] or "Unspecified" for row in rows], [row["count"] for row in rows], "High Risk Programmes")


def _recent_alerts(filters, limit=20):
    alerts = _alert_queryset(filters)
    if alerts is None:
        return []
    return [
        {
            "id": item["id"],
            "programme": item["programme"],
            "trigger_type": item["trigger_type"],
            "severity": item["severity"],
            "status": item["status"],
            "message": item["message"],
            "created_at": item["created_at"],
        }
        for item in alerts.order_by("-created_at").values("id", "programme", "trigger_type", "severity", "status", "message", "created_at")[:limit]
    ]


def _recommended_actions(filters):
    CorrectiveAction = safe_model_import("accreditation", "CorrectiveAction")
    if CorrectiveAction is None:
        return []
    actions = apply_faculty_department_filters(CorrectiveAction.objects.select_related("cycle", "component"), filters)
    return list(actions.exclude(status__in=["verified", "closed"]).values("id", "title", "programme", "priority", "status", "deadline")[:20])


def get_activity_feed(filters):
    limit = filters.get("limit", 20)
    activities = []
    Evidence = safe_model_import("accreditation", "Evidence")
    Alert = safe_model_import("accreditation", "EarlyWarningAlert")
    Document = safe_model_import("documents", "InstitutionalDocument")
    ExamQualityReport = safe_model_import("examinations", "ExamQualityReport")
    Feedback = safe_model_import("students", "StudentFeedback")

    if Alert is not None:
        alerts = apply_faculty_department_filters(Alert.objects.select_related("cycle"), filters).order_by("-created_at")[:limit]
        for alert in alerts:
            activities.append(_activity(f"alert-{alert.id}", "accreditation_alert", alert.message, alert.programme, "accreditation", alert.severity, alert.created_at))
    if Evidence is not None:
        evidence = apply_faculty_department_filters(Evidence.objects.select_related("cycle"), filters).order_by("-upload_date")[:limit]
        for item in evidence:
            activities.append(_activity(f"evidence-{item.id}", "evidence_uploaded", item.title, item.programme, "accreditation", item.verification_status, item.upload_date, item.uploaded_by))
    if Document is not None:
        docs = _apply_date_filters(Document.objects.select_related("uploaded_by").order_by("-created_at"), filters, "created_at")[:limit]
        for doc in docs:
            activities.append(_activity(f"document-{doc.id}", "document_activity", doc.title, doc.status, "documents", doc.status, doc.created_at, doc.uploaded_by))
    if ExamQualityReport is not None:
        reports = _apply_date_filters(ExamQualityReport.objects.select_related("student", "exam_session").order_by("-submitted_at"), filters, "submitted_at")[:limit]
        for report in reports:
            activities.append(_activity(f"exam-report-{report.id}", "examination_quality_report", report.exam_session.course_code_title, "Quality report submitted", "examinations", "", report.submitted_at, report.student))
    if Feedback is not None:
        feedback = _apply_date_filters(Feedback.objects.select_related("submitted_by").order_by("-submitted_at"), filters, "submitted_at")[:limit]
        for item in feedback:
            activities.append(_activity(f"feedback-{item.id}", "student_feedback", item.category, "Student feedback submitted", "students", item.urgency, item.submitted_at, item.submitted_by))
    return sorted(activities, key=lambda item: item["created_at"], reverse=True)[:limit]


def _activity(item_id, activity_type, title, description, module, severity, created_at, actor=None):
    return {
        "id": str(item_id),
        "type": activity_type,
        "title": title,
        "description": description,
        "module": module,
        "severity": severity or "",
        "created_at": created_at,
        "actor": {
            "id": getattr(actor, "id", None),
            "name": getattr(actor, "get_full_name", lambda: "")() or getattr(actor, "username", ""),
        } if actor else None,
    }


def get_dashboard_summary(filters):
    overview = get_university_overview(filters)
    accreditation = get_accreditation_dashboard(filters)
    teaching = get_teaching_learning_dashboard(filters)
    examinations = get_examination_dashboard(filters)
    documents = get_documents_dashboard(filters)
    students = get_student_experience_dashboard(filters)
    early_warning = get_early_warning_dashboard(filters)
    return {
        "filters": filters,
        "kpi_cards": [
            _kpi("average_pari", "Average PARI Score", overview["kpis"]["average_pari_score"], "%", status_from_score(overview["kpis"]["average_pari_score"])),
            _kpi("accreditation_ready_programmes", "Accreditation Ready Programmes", overview["kpis"]["programmes_accreditation_ready"]),
            _kpi("moderate_risk_programmes", "Moderate Risk Programmes", overview["kpis"]["programmes_moderate_risk"]),
            _kpi("high_risk_programmes", "High Risk Programmes", overview["kpis"]["programmes_high_risk"], "", "high_risk"),
            _kpi("active_qa_committees", "Active QA Committees", overview["kpis"]["active_qa_committees"]),
            _kpi("average_qacei_score", "Average QACEI Score", overview["kpis"]["average_qacei_score"], "%"),
            _kpi("open_critical_findings", "Open Critical Findings", overview["kpis"]["open_critical_findings"], "", "critical"),
            _kpi("overdue_recommendations", "Overdue Recommendations", overview["kpis"]["overdue_recommendations"]),
            _kpi("pending_evidence_verification", "Pending Evidence Verification", overview["kpis"]["pending_evidence_verifications"]),
            _kpi("lecture_delivery_rate", "Lecture Delivery Rate", teaching.get("average_lecture_delivery_rate", 0), "%"),
            _kpi("examination_quality_score", "Examination Quality Score", examinations.get("overall_examination_quality_score", 0), "/5"),
            _kpi("document_completeness", "Document Completeness", documents.get("document_completeness_percentage", 0), "%"),
            _kpi("student_satisfaction_score", "Student Satisfaction Score", students.get("average_student_satisfaction_score", 0), "%"),
        ],
        "charts": {
            "risk_distribution": early_warning.get("charts", {}).get("risk_category_distribution_pie", build_chart("pie", [], [], "Risk")),
            "accreditation_readiness": accreditation.get("charts", {}).get("readiness_distribution_pie", build_chart("pie", [], [], "Programmes")),
            "documents_status": documents.get("charts", {}).get("document_status_pie", build_chart("pie", [], [], "Documents")),
        },
        "alerts": early_warning.get("recent_alerts", []),
        "recent_activity": get_activity_feed(filters),
        "quick_links": [
            {"label": "Accreditation", "endpoint": "/api/dashboards/accreditation/"},
            {"label": "Early Warning", "endpoint": "/api/dashboards/early-warning/"},
            {"label": "Documents", "endpoint": "/api/dashboards/documents/"},
        ],
    }


def _kpi(key, label, value, unit="", status=""):
    return {"key": key, "label": label, "value": number(value), "unit": unit, "status": status, "change": None}
