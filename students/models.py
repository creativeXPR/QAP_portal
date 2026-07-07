from django.db import models

# Create your models here.
class StudentFeedback(models.Model):
    student_name = models.CharField(max_length=100)
    student_email = models.EmailField(default='', blank=True, null=True)
    feedback_text = models.TextField()
    category = models.CharField(max_length=50) # complaint, suggestion, inquiry, etc.
    classification = models.CharField(max_length=50, default='academic') # academic, administrative, etc.
    status = models.CharField(max_length=20, default='pending') # pending, in_progress, resolved
    urgency = models.CharField(max_length=20, default='normal') # normal, high, critical
    submitted_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"Feedback from {self.student_name} at {self.submitted_at}"