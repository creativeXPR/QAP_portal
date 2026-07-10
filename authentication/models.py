from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import PROFILE_STATUS_CHOICES


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=PROFILE_STATUS_CHOICES, default='student')
    profile_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile({self.user.username})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile if it exists. Defensive to handle pre-existing users."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
