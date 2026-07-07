from django.contrib import admin
from .models import LecturerProfile, AssessmentReport


@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "staff_id", "rank")
    list_filter = ("department", "rank")
    search_fields = ("user__username", "user__first_name", "user__last_name", "staff_id")


@admin.register(AssessmentReport)
class AssessmentReportAdmin(admin.ModelAdmin):
    list_display = (
        "lecturer", "course", "student", "academic_session",
        "semester", "average_rating", "included_in_dossier", "submitted_at",
    )
    list_filter = ("academic_session", "semester", "included_in_dossier")
    search_fields = ("lecturer__user__username", "lecturer__staff_id", "course__code")
    autocomplete_fields = ["lecturer", "course"]
    date_hierarchy = "submitted_at"