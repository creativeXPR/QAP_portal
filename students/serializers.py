from rest_framework import serializers

from .models import Student, StudentFeedback, StudentFeedbackAttachment, StudentFeedbackUpdate, StudentNotification
from .permissions import MANAGER_ROLES, role_for


ALLOWED_ATTACHMENT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_ATTACHMENT_SIZE = 1024 * 1024


def get_uploaded_attachments(request):
    if not request:
        return []
    files = []
    for key in ("attachments", "attachments[]", "attachment_uploads"):
        files.extend(request.FILES.getlist(key))
    return files


def validate_feedback_attachment(file_obj):
    name = getattr(file_obj, "name", "")
    extension = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_ATTACHMENT_EXTENSIONS))
        raise serializers.ValidationError(f"Unsupported file type. Allowed extensions: {allowed}.")
    if getattr(file_obj, "size", 0) > MAX_ATTACHMENT_SIZE:
        raise serializers.ValidationError("Attachment must not exceed 1MB.")


def create_feedback_attachments(complaint, files, user):
    return [
        StudentFeedbackAttachment.objects.create(
            complaint=complaint,
            file=file_obj,
            original_name=getattr(file_obj, "name", ""),
            content_type=getattr(file_obj, "content_type", "") or "",
            size=getattr(file_obj, "size", 0) or 0,
            uploaded_by=user if getattr(user, "is_authenticated", False) else None,
        )
        for file_obj in files
    ]


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


class StudentFeedbackAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = StudentFeedbackAttachment
        fields = ["id", "original_name", "content_type", "size", "url", "uploaded_by", "uploaded_at"]
        read_only_fields = fields

    def get_url(self, obj):
        if not obj.file:
            return ""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class StudentFeedbackSerializer(serializers.ModelSerializer):
    student = serializers.CharField(source="student_name")
    feedback = serializers.CharField(source="feedback_text")
    submitted_by = serializers.PrimaryKeyRelatedField(read_only=True)
    submitted_by_username = serializers.CharField(source="submitted_by.username", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    updated_by_username = serializers.CharField(source="updated_by.username", read_only=True)
    updates = StudentFeedbackUpdateSerializer(many=True, read_only=True)
    notification_history = StudentFeedbackNotificationSerializer(source="notifications", many=True, read_only=True)
    attachments = StudentFeedbackAttachmentSerializer(many=True, read_only=True)

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
            "submission_mode",
            "admin_comment",
            "assigned_to",
            "assigned_to_username",
            "updated_by",
            "updated_by_username",
            "submitted_at",
            "updated_at",
            "updates",
            "notification_history",
            "attachments",
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
            "attachments",
        ]

    def validate_category(self, value):
        allowed = {choice.value for choice in StudentFeedback.Category}
        if value not in allowed:
            raise serializers.ValidationError("Select a valid category.")
        return value

    def validate_classification(self, value):
        allowed = {choice.value for choice in StudentFeedback.Classification}
        if value not in allowed:
            raise serializers.ValidationError("Select a valid classification.")
        return value

    def validate_urgency(self, value):
        allowed = {choice.value for choice in StudentFeedback.Urgency}
        if value not in allowed:
            raise serializers.ValidationError("Select a valid urgency.")
        return value

    def validate_submission_mode(self, value):
        allowed = {choice.value for choice in StudentFeedback.SubmissionMode}
        if value not in allowed:
            raise serializers.ValidationError("Select a valid submission mode.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        is_manager = role_for(getattr(request, "user", None)) in MANAGER_ROLES if request else False
        attachment_errors = []
        for file_obj in get_uploaded_attachments(request):
            try:
                validate_feedback_attachment(file_obj)
            except serializers.ValidationError as exc:
                attachment_errors.append({getattr(file_obj, "name", "attachment"): exc.detail})
        if attachment_errors:
            raise serializers.ValidationError({"attachments": attachment_errors})

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

    def create(self, validated_data):
        complaint = super().create(validated_data)
        request = self.context.get("request")
        create_feedback_attachments(complaint, get_uploaded_attachments(request), getattr(request, "user", None))
        return complaint

    def update(self, instance, validated_data):
        complaint = super().update(instance, validated_data)
        request = self.context.get("request")
        create_feedback_attachments(complaint, get_uploaded_attachments(request), getattr(request, "user", None))
        return complaint
