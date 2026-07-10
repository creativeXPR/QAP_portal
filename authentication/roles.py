from .constants import DELETE_PROFILE_STATUSES, MANAGER_PROFILE_STATUSES


MANAGER_ROLES = MANAGER_PROFILE_STATUSES
DELETE_ROLES = DELETE_PROFILE_STATUSES


def role_for(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if user.is_superuser or user.is_staff:
        return "admin"
    profile = getattr(user, "profile", None)
    return getattr(profile, "status", None)