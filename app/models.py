from django.contrib.auth.models import AbstractUser
from django.db import models


from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('master_admin', 'Master Admin'),
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('gd_munsi', 'GD Munsi'),
        ('field_staff', 'Field Staff'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Who created this user?
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users"
    )

    # GD Munsi belongs to exactly ONE admin
    admin = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gd_munsi_admin",
        limit_choices_to={'role': 'admin'}
    )

    # Field staff belong to exactly ONE GD Munsi
    gd_munsi = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="field_staffs",
        limit_choices_to={'role': 'gd_munsi'}
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
