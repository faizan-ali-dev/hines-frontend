from django.contrib.auth.models import AbstractUser
from django.db import models


class ClientUser(AbstractUser):
    """The account used by the client signup and dashboard experience."""

    class AssignmentStatus(models.TextChoices):
        DEMO = "demo", "Demo"
        CLIENT = "client", "Client"

    email = models.EmailField(unique=True)
    referral_code = models.CharField(max_length=100, blank=True)
    demo_progress = models.PositiveSmallIntegerField(default=0)
    client_progress = models.PositiveSmallIntegerField(default=0)
    carried_demo_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    client_activated_at = models.DateTimeField(blank=True, null=True)
    assignment_status = models.CharField(max_length=10, choices=AssignmentStatus.choices, default=AssignmentStatus.DEMO)

    @property
    def full_name(self):
        return " ".join(part for part in (self.first_name, self.last_name) if part).strip()

    @property
    def client_is_active(self):
        return self.assignment_status == self.AssignmentStatus.CLIENT


class DemoUser(ClientUser):
    class Meta:
        proxy = True
        verbose_name = "Demo User"
        verbose_name_plural = "Demo Users"


class ActiveClientUser(ClientUser):
    class Meta:
        proxy = True
        verbose_name = "Client User"
        verbose_name_plural = "Client Users"

class SiteSetting(models.Model):
    facebook_url = models.URLField(blank=True, default="")
    twitter_url = models.URLField(blank=True, default="")
    linkedin_url = models.URLField(blank=True, default="")
    instagram_url = models.URLField(blank=True, default="")
    youtube_url = models.URLField(blank=True, default="")
    
    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"
