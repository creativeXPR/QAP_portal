from datetime import date, datetime


def _number(value):
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def safe_divide(numerator, denominator, multiplier=1):
    """Return None for missing values or division by zero."""
    numerator = _number(numerator)
    denominator = _number(denominator)
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator * multiplier


def staff_to_student_ratio(values):
    return safe_divide(values.get("total_students"), values.get("total_academic_staff"))


def phd_staff_percentage(values):
    return safe_divide(values.get("staff_with_phd"), values.get("total_academic_staff"), 100)


def nuc_minimum_compliance(values):
    return safe_divide(values.get("staff_meeting_nuc_requirement"), values.get("required_staff"), 100)


def lecture_delivery_rate(values):
    return safe_divide(values.get("lectures_held"), values.get("lectures_scheduled"), 100)


def course_coverage(values):
    return safe_divide(values.get("topics_completed"), values.get("topics_planned"), 100)


def curriculum_compliance(values):
    return safe_divide(values.get("ccmass_aligned_courses"), values.get("total_courses"), 100)


def student_satisfaction_index(values):
    return safe_divide(values.get("total_student_rating"), values.get("maximum_possible_rating"), 100)


def retention_rate(values):
    return safe_divide(values.get("returning_students"), values.get("total_students"), 100)


def pass_rate(values):
    return safe_divide(values.get("students_passed"), values.get("students_examined"), 100)


def malpractice_rate(values):
    return safe_divide(values.get("cases"), values.get("candidates"), 1000)


def result_release_turnaround_time(values):
    exam_date = _date(values.get("exam_date"))
    release_date = _date(values.get("result_release_date"))
    if exam_date is None or release_date is None:
        return None
    return (release_date - exam_date).days


def functionality_rate(values):
    return safe_divide(values.get("functional_equipment"), values.get("total_equipment"), 100)


def current_text_percentage(values):
    return safe_divide(values.get("core_texts_under_5_years"), values.get("total_core_texts"), 100)


def library_usage_rate(values):
    return safe_divide(values.get("students_using_library"), values.get("total_students"), 100)


def seating_capacity_utilization(values):
    return safe_divide(values.get("number_of_students"), values.get("available_seats"), 100)


def internet_uptime(values):
    return safe_divide(values.get("hours_available"), values.get("total_required_hours"), 100)


def publications_per_staff(values):
    return safe_divide(values.get("total_publications"), values.get("total_academic_staff"))


def postgraduate_supervision_completion_rate(values):
    return safe_divide(values.get("completed_supervisions"), values.get("total_supervisions"), 100)


def complaint_resolution_rate(values):
    return safe_divide(values.get("resolved_complaints"), values.get("total_complaints"), 100)


def average_complaint_resolution_time(values):
    return safe_divide(values.get("sum_resolution_time"), values.get("total_resolved_complaints"))


def qacei(values):
    return safe_divide(values.get("total_qa_score"), values.get("maximum_possible_score"), 5)


FORMULAS = {
    "staff_to_student_ratio": staff_to_student_ratio,
    "phd_staff_percentage": phd_staff_percentage,
    "nuc_minimum_compliance": nuc_minimum_compliance,
    "lecture_delivery_rate": lecture_delivery_rate,
    "course_coverage": course_coverage,
    "curriculum_compliance": curriculum_compliance,
    "student_satisfaction_index": student_satisfaction_index,
    "retention_rate": retention_rate,
    "pass_rate": pass_rate,
    "malpractice_rate": malpractice_rate,
    "result_release_turnaround_time": result_release_turnaround_time,
    "functionality_rate": functionality_rate,
    "current_text_percentage": current_text_percentage,
    "library_usage_rate": library_usage_rate,
    "seating_capacity_utilization": seating_capacity_utilization,
    "internet_uptime": internet_uptime,
    "publications_per_staff": publications_per_staff,
    "postgraduate_supervision_completion_rate": postgraduate_supervision_completion_rate,
    "complaint_resolution_rate": complaint_resolution_rate,
    "average_complaint_resolution_time": average_complaint_resolution_time,
    "qacei": qacei,
}


def calculate_formula(formula_key, values):
    formula = FORMULAS.get(formula_key)
    if formula is None:
        return None
    result = formula(values)
    return round(result, 2) if result is not None else None
