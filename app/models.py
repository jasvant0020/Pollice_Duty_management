from django.db import models

# Create your models here.
# app/models.py
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("custom_admin", "Custom Admin"),
        ("gd_munsi", "GD Munsi"),
        ("police", "Police"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="police")

    def __str__(self):
        return self.username

