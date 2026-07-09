from django.db import models

class KPI(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    embedlink = models.TextField()
    metrics = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "KPI"
        verbose_name_plural = "KPIs"