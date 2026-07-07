from django.db import models


class Faculty(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name_plural = "Faculties"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=150)

    class Meta:
        unique_together = ("faculty", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.faculty.name})"