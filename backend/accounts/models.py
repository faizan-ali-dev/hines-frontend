from django.contrib.auth.models import AbstractUser
from django.db import models


class ClientUser(AbstractUser):
    """The account used by the client signup and dashboard experience."""

    email = models.EmailField(unique=True)
    referral_code = models.CharField(max_length=100, blank=True)
    demo_progress = models.PositiveSmallIntegerField(default=0)
    client_progress = models.PositiveSmallIntegerField(default=0)
    carried_demo_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    client_activated_at = models.DateTimeField(blank=True, null=True)

    @property
    def full_name(self):
        return " ".join(part for part in (self.first_name, self.last_name) if part).strip()

    @property
    def client_is_active(self):
        return self.client_activated_at is not None

# Create your models here.
