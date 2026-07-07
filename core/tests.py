from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Department, Faculty


class CoreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="core_user", password="password")
        self.client.force_authenticate(self.user)

    def test_faculty_and_department_crud(self):
        response = self.client.post("/api/core/faculties/", {"name": "Faculty of Science"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        faculty_id = response.data["id"]

        response = self.client.post(
            "/api/core/departments/",
            {"faculty": faculty_id, "name": "Computer Science"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Department.objects.count(), 1)

        response = self.client.get("/api/core/departments/", {"search": "Computer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self.client.patch(
            f"/api/core/departments/{response.data[0]['id']}/",
            {"name": "Computer Science and Informatics"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Department.objects.get().name, "Computer Science and Informatics")

    def test_core_requires_authentication_and_validates_duplicates(self):
        faculty = Faculty.objects.create(name="Faculty of Arts")
        response = self.client.post("/api/core/faculties/", {"name": faculty.name}, format="json")
        self.assertEqual(response.status_code, 400)

        anonymous = APIClient()
        response = anonymous.get("/api/core/faculties/")
        self.assertIn(response.status_code, [401, 403])
