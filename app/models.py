from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # add extra fields if needed
    pass

class SecurityCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    total_personnel = models.PositiveIntegerField()
    personnel_by_rank = models.JSONField(default=dict, blank=True)  # e.g., {"SP": 2, "Addl SP": 3}

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
