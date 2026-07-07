from rest_framework import serializers

from .models import Student, StudentFeedback


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


class StudentFeedbackSerializer(serializers.ModelSerializer):
    student = serializers.CharField(source="student_name")
    feedback = serializers.CharField(source="feedback_text")
    submitted_by = serializers.PrimaryKeyRelatedField(read_only=True)
    submitted_by_username = serializers.CharField(source="submitted_by.username", read_only=True)

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
            "submitted_at",
        ]
        read_only_fields = ["id", "submitted_by", "submitted_by_username", "status", "submitted_at"]
