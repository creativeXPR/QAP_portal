from rest_framework.permissions import SAFE_METHODS, BasePermission


ADMIN_ROLES = {"admin", "super_admin", "dqa_admin", "principle_officer"}
COMMITTEE_MANAGER_ROLES = {"committee_chairperson", "committee_secretary", "qa_focal_person", "focal_person"}
VIEWER_ROLES = {"committee_member", "department_admin", "faculty_admin", "read_only_viewer"}


def role_for(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if user.is_superuser or user.is_staff:
        return "admin"
    profile = getattr(user, "profile", None)
    return getattr(profile, "status", None)


def is_committee_member(user, committee):
    if not getattr(user, "is_authenticated", False) or not committee:
        return False
    return committee.members.filter(user=user, is_active=True).exists()


def is_committee_manager(user, committee):
    if role_for(user) in ADMIN_ROLES:
        return True
    if not committee:
        return role_for(user) in COMMITTEE_MANAGER_ROLES
    return committee.members.filter(user=user, is_active=True, role__in=["chairperson", "secretary", "qa_focal_person"]).exists()


class QACommitteePermission(BasePermission):
    def has_permission(self, request, view):
        role = role_for(request.user)
        if role in ADMIN_ROLES:
            return True
        if request.method in SAFE_METHODS:
            return role in COMMITTEE_MANAGER_ROLES | VIEWER_ROLES
        return role in COMMITTEE_MANAGER_ROLES

    def has_object_permission(self, request, view, obj):
        role = role_for(request.user)
        if role in ADMIN_ROLES:
            return True
        committee = _committee_for(obj)
        if request.method in SAFE_METHODS:
            return is_committee_member(request.user, committee) or role in COMMITTEE_MANAGER_ROLES
        return is_committee_manager(request.user, committee)


class EvidenceVerificationPermission(QACommitteePermission):
    def has_object_permission(self, request, view, obj):
        if role_for(request.user) in ADMIN_ROLES:
            return True
        committee = obj.action_plan.recommendation.audit_cycle.committee
        return is_committee_manager(request.user, committee)


def _committee_for(obj):
    if hasattr(obj, "committee"):
        return obj.committee
    if hasattr(obj, "meeting"):
        return obj.meeting.committee
    if hasattr(obj, "audit_cycle"):
        return obj.audit_cycle.committee
    if hasattr(obj, "recommendation"):
        return obj.recommendation.audit_cycle.committee
    if hasattr(obj, "action_plan"):
        return obj.action_plan.recommendation.audit_cycle.committee
    if hasattr(obj, "finding") and obj.finding:
        return obj.finding.audit_cycle.committee
    return None
