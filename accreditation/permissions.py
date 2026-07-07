from rest_framework.permissions import SAFE_METHODS, BasePermission


FULL_ACCESS_ROLES = {"admin", "principle_officer"}
SUBMITTER_ROLES = {"focal_person", "admin", "principle_officer"}


def user_role(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if user.is_superuser or user.is_staff:
        return "admin"
    profile = getattr(user, "profile", None)
    return getattr(profile, "status", None)


class AccreditationPermission(BasePermission):
    def has_permission(self, request, view):
        if not getattr(request.user, "is_authenticated", False):
            return False
        role = user_role(request.user)
        if request.method in SAFE_METHODS:
            return True
        if role in FULL_ACCESS_ROLES:
            return True
        if getattr(view, "action", None) in {"progress", "submit"}:
            return role in SUBMITTER_ROLES
        return role in SUBMITTER_ROLES
