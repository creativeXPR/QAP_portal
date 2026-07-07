from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Profile


class RegistrationTests(TestCase):
    def test_registration_reuses_signal_created_profile(self):
        client = APIClient()
        response = client.post(
            "/api/auth/google/register/",
            {
                "username": "dqa_admin",
                "email": "dqa_admin@example.com",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
                "status": "admin",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        user = get_user_model().objects.get(username="dqa_admin")
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(user.profile.status, "admin")
        self.assertTrue(user.profile.profile_complete)
        self.assertIn("access", response.data)
