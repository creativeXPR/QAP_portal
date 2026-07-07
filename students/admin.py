from django.contrib import admin
from .models import Student, StudentFeedback


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("matric_number", "first_name", "last_name", "email", "department", "level", "status")
    list_filter = ("faculty", "department", "level", "status")
    search_fields = ("matric_number", "first_name", "last_name", "email")
    filter_horizontal = ("courses",)


@admin.register(StudentFeedback)
class StudentFeedbackAdmin(admin.ModelAdmin):
    list_display = ("student_name", "category", "urgency", "status", "submitted_by", "submitted_at")
    list_filter = ("category", "urgency", "status")
    search_fields = ("student_name", "feedback_text", "submitted_by__username")
