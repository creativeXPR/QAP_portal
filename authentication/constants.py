PROFILE_STATUS_CHOICES = [
    ("student", "Student"),
    ("staff", "Staff"),
    ("focal_person", "Focal Person"),
    ("principle_officer", "Principle Officer"),
    ("admin", "Administrator"),
]

PROFILE_STATUS_VALUES = {value for value, _ in PROFILE_STATUS_CHOICES}
MANAGER_PROFILE_STATUSES = frozenset({"admin", "principle_officer", "focal_person"})
DELETE_PROFILE_STATUSES = frozenset({"admin", "principle_officer"})


def profile_status_options():
    return [
        {
            "value": value,
            "label": label,
            "is_manager": value in MANAGER_PROFILE_STATUSES,
            "is_admin": value == "admin",
        }
        for value, label in PROFILE_STATUS_CHOICES
    ]