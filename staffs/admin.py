from django.contrib import admin
from .models import Staff, StaffFeedback, StaffFeedbackUpdate, StaffNotification


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "first_name", "last_name", "email", "department", "role", "status")
    list_filter = ("faculty", "department", "role", "status")
    search_fields = ("staff_id", "first_name", "last_name", "email", "role")
    filter_horizontal = ("courses",)


@admin.register(StaffFeedback)
class StaffFeedbackAdmin(admin.ModelAdmin):
    list_display = ("staff_name", "category", "urgency", "status", "assigned_to", "updated_by", "submitted_by", "submitted_at", "updated_at")
    list_filter = ("category", "classification", "urgency", "status", "assigned_to")
    search_fields = ("staff_name", "feedback_text", "admin_comment", "submitted_by__username", "assigned_to__username")


@admin.register(StaffFeedbackUpdate)
class StaffFeedbackUpdateAdmin(admin.ModelAdmin):
    list_display = ("complaint", "previous_status", "new_status", "assigned_to", "updated_by", "created_at")
    list_filter = ("previous_status", "new_status", "assigned_to", "updated_by")
    search_fields = ("complaint__staff_name", "admin_comment", "updated_by__username")


@admin.register(StaffNotification)
class StaffNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "complaint", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username", "complaint__staff_name")
