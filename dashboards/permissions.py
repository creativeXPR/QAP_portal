from rest_framework.permissions import BasePermission


DASHBOARD_ROLES = {
    "admin",
    "principle_officer",
    "focal_person",
    "dqa_admin",
    "super_admin",
    "qa_focal_person",
    "committee_chairperson",
    "committee_secretary",
    "committee_member",
    "department_admin",
    "faculty_admin",
    "read_only_viewer",
}


def dashboard_role(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if user.is_superuser or user.is_staff:
        return "admin"
    profile = getattr(user, "profile", None)
    return getattr(profile, "status", None)


class DashboardPermission(BasePermission):
    def has_permission(self, request, view):
        role = dashboard_role(request.user)
        if role not in DASHBOARD_ROLES:
            return False
        if role == "department_admin":
            return _matches_scope(request, "department_id")
        if role == "faculty_admin":
            return _matches_scope(request, "faculty_id")
        return True


def _matches_scope(request, scope_key):
    requested_id = request.query_params.get(scope_key)
    if not requested_id:
        return False
    try:
        requested_id = int(requested_id)
    except (TypeError, ValueError):
        return False
    try:
        student_record = request.user.student_record
    except Exception:
        student_record = None
    if scope_key == "department_id":
        return getattr(student_record, "department_id", None) == requested_id
    if scope_key == "faculty_id":
        return getattr(student_record, "faculty_id", None) == requested_id
    return False
