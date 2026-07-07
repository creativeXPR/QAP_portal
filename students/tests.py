from django.test import TestCase
from .serializers import StudentFeedbackSerializer


class StudentFeedbackSerializerTests(TestCase):
    def test_serializer_accepts_frontend_feedback_fields(self):
        payload = {
            "student": "demo_user",
            "feedback": "This is a test feedback.",
            "category": "complaint",
        }

        serializer = StudentFeedbackSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["student_name"], "demo_user")
        self.assertEqual(serializer.validated_data["feedback_text"], "This is a test feedback.")
