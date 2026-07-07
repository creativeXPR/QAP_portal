from django.contrib import admin
from .models import ExamSession, ExamQualityReport


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ("course_code_title", "department", "exam_date", "venue", "academic_session")
    list_filter = ("department", "academic_session")
    search_fields = ("course_code_title", "venue")
    date_hierarchy = "exam_date"


@admin.register(ExamQualityReport)
class ExamQualityReportAdmin(admin.ModelAdmin):
    list_display = (
        "exam_session", "student", "overall_rating",
        "observed_misconduct", "submitted_at",
    )
    list_filter = ("observed_misconduct",)
    search_fields = ("exam_session__course_code_title",)
    autocomplete_fields = ["exam_session"]
    date_hierarchy = "submitted_at"