from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):

    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('master_admin', 'Master Admin'),
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('gd_munsi', 'GD Munsi'),
        ('field_staff', 'Field Staff'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    created_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="children"
    )

    admin_owner = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="admin_users"
    )

    gd_munsi_owner = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="gd_staffs"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

# class SecurityCategory(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     total_personnel = models.PositiveIntegerField()
#     personnel_by_rank = models.JSONField(default=dict, blank=True)  # e.g., {"SP": 2, "Addl SP": 3}

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name
