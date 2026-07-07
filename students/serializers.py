from rest_framework import serializers

from .models import Student, StudentFeedback, StudentFeedbackUpdate, StudentNotification
from .permissions import MANAGER_ROLES, role_for


class StudentSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source="faculty.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    course_codes = serializers.SlugRelatedField(source="courses", slug_field="code", many=True, read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "user",
            "matric_number",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "faculty",
            "faculty_name",
            "department",
            "department_name",
            "programme",
            "level",
            "status",
            "courses",
            "course_codes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "full_name", "faculty_name", "department_name", "course_codes"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate_matric_number(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        faculty = attrs.get("faculty") or getattr(self.instance, "faculty", None)
        department = attrs.get("department") or getattr(self.instance, "department", None)
        courses = attrs.get("courses")

        if faculty and department and department.faculty_id != faculty.id:
            raise serializers.ValidationError({"department": ["Department must belong to the selected faculty."]})

        if courses and department:
            mismatched = [course.code for course in courses if course.department_id != department.id]
            if mismatched:
                raise serializers.ValidationError(
                    {"courses": [f"Courses must belong to the selected department: {', '.join(mismatched)}."]}
                )
        return attrs


class StudentFeedbackUpdateSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source="updated_by.username", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)

    class Meta:
        model = StudentFeedbackUpdate
        fields = [
            "id",
            "previous_status",
            "new_status",
            "admin_comment",
            "assigned_to",
            "assigned_to_username",
            "updated_by",
            "updated_by_username",
            "created_at",
        ]
        read_only_fields = fields


class StudentNotificationSerializer(serializers.ModelSerializer):
    complaint_id = serializers.IntegerField(source="complaint.id", read_only=True)

    class Meta:
        model = StudentNotification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "user",
            "complaint",
            "complaint_id",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "title", "message", "notification_type", "user", "complaint", "complaint_id", "created_at"]


class StudentFeedbackNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentNotification
        fields = ["id", "title", "message", "notification_type", "is_read", "created_at"]
        read_only_fields = fields


class StudentFeedbackSerializer(serializers.ModelSerializer):
    student = serializers.CharField(source="student_name")
    feedback = serializers.CharField(source="feedback_text")
    submitted_by = serializers.PrimaryKeyRelatedField(read_only=True)
    submitted_by_username = serializers.CharField(source="submitted_by.username", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    updated_by_username = serializers.CharField(source="updated_by.username", read_only=True)
    updates = StudentFeedbackUpdateSerializer(many=True, read_only=True)
    notification_history = StudentFeedbackNotificationSerializer(source="notifications", many=True, read_only=True)

    class Meta:
        model = StudentFeedback
        fields = [
            "id",
            "submitted_by",
            "submitted_by_username",
            "student",
            "student_email",
            "feedback",
            "category",
            "classification",
            "status",
            "urgency",
            "admin_comment",
            "assigned_to",
            "assigned_to_username",
            "updated_by",
            "updated_by_username",
            "submitted_at",
            "updated_at",
            "updates",
            "notification_history",
        ]
        read_only_fields = [
            "id",
            "submitted_by",
            "submitted_by_username",
            "assigned_to_username",
            "updated_by",
            "updated_by_username",
            "submitted_at",
            "updated_at",
            "updates",
            "notification_history",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        is_manager = role_for(getattr(request, "user", None)) in MANAGER_ROLES if request else False
        if self.instance is None:
            forbidden_fields = []
            if attrs.get("status") and attrs["status"] != StudentFeedback.Status.PENDING:
                forbidden_fields.append("status")
            if attrs.get("admin_comment"):
                forbidden_fields.append("admin_comment")
            if attrs.get("assigned_to"):
                forbidden_fields.append("assigned_to")
            if forbidden_fields and not is_manager:
                raise serializers.ValidationError(
                    {field: ["Only authorized staff can set this field when creating a complaint."] for field in forbidden_fields}
                )
            attrs["status"] = StudentFeedback.Status.PENDING
        elif not is_manager:
            protected_fields = {"status", "admin_comment", "assigned_to"}
            attempted = protected_fields.intersection(attrs)
            if attempted:
                raise serializers.ValidationError(
                    {field: ["Only authorized staff can update this field."] for field in attempted}
                )
        return attrs
