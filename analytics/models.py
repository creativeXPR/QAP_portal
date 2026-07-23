from django.db import models

class KPI(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    embedlink = models.TextField()
    category = models.CharField(max_length=255, default='academic')
    metrics = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, default='guest')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "KPI"
        verbose_name_plural = "KPIs"