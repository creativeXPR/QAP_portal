from django.contrib import admin
from .models import Student, StudentFeedback, StudentFeedbackAttachment, StudentFeedbackUpdate, StudentNotification


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("matric_number", "first_name", "last_name", "email", "department", "level", "status")
    list_filter = ("faculty", "department", "level", "status")
    search_fields = ("matric_number", "first_name", "last_name", "email")
    filter_horizontal = ("courses",)


@admin.register(StudentFeedback)
class StudentFeedbackAdmin(admin.ModelAdmin):
    list_display = ("student_name", "category", "urgency", "status", "assigned_to", "updated_by", "submitted_by", "submitted_at", "updated_at")
    list_filter = ("category", "classification", "urgency", "status", "assigned_to")
    search_fields = ("student_name", "feedback_text", "admin_comment", "submitted_by__username", "assigned_to__username")


@admin.register(StudentFeedbackAttachment)
class StudentFeedbackAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "complaint", "content_type", "size", "uploaded_by", "uploaded_at")
    list_filter = ("content_type", "uploaded_at")
    search_fields = ("original_name", "complaint__student_name", "uploaded_by__username")


@admin.register(StudentFeedbackUpdate)
class StudentFeedbackUpdateAdmin(admin.ModelAdmin):
    list_display = ("complaint", "previous_status", "new_status", "assigned_to", "updated_by", "created_at")
    list_filter = ("previous_status", "new_status", "assigned_to", "updated_by")
    search_fields = ("complaint__student_name", "admin_comment", "updated_by__username")


@admin.register(StudentNotification)
class StudentNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "complaint", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username", "complaint__student_name")
