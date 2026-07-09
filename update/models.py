from django.db import models

class Update(models.Model):
    category = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    classification = models.CharField(max_length=255)
    forUser = models.CharField(max_length=255, default='all')  # e.g., 'all', 'students', 'principal_officer', etc.
    button = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title
