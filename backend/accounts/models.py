from django.contrib.auth.models import AbstractUser
from django.db import models


class ClientUser(AbstractUser):
    """The account used by the client signup and dashboard experience."""

    email = models.EmailField(unique=True)
    referral_code = models.CharField(max_length=100, blank=True)

    @property
    def full_name(self):
        return " ".join(part for part in (self.first_name, self.last_name) if part).strip()

# Create your models here.
