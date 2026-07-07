# courses/admin.py
from django.contrib import admin
from .models import Course, LectureSession


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "department")
    search_fields = ("code", "title")
    list_filter = ("department",)


@admin.register(LectureSession)
class LectureSessionAdmin(admin.ModelAdmin):
    list_display = (
        "course", "monitored_at", "time_slot", "held",
        "lecturer_present", "estimated_attendance", "respondent",
    )
    list_filter = ("held", "mode", "level", "reason_not_held")
    search_fields = ("course__code", "course__title", "venue")
    date_hierarchy = "monitored_at"
    autocomplete_fields = ["course"]