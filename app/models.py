from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.conf import settings


class User(AbstractUser):

    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('master_admin', 'Master Admin'),
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('gd_munsi', 'GD Munsi'),
        ('field_staff', 'Field Staff'),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^[0-9]{10}$', 'Enter a valid 10-digit phone number')],
        null=True, blank=True
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    rank = models.CharField(max_length=150, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users"
    )

    # GD Munsi → ONE Admin
    admin = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gd_munsi_admin",
        limit_choices_to={'role': 'admin'}
    )

    # Field staff → ONE GD
    gd_munsi = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="field_staffs",
        limit_choices_to={'role': 'gd_munsi'}
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["admin"],
                condition=Q(role="gd_munsi"),
                name="one_gd_per_admin"
            )
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"



class SecurityCategory(models.Model):
    name = models.CharField(max_length=100)
    total_personnel = models.PositiveIntegerField(default=0)
    personnel_by_rank = models.JSONField(default=dict, blank=True)

    # 🔐 Owner admin
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_categories",
        limit_choices_to={"role": "admin"}
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "admin")  # same name allowed for different admins

    def __str__(self):
        return f"{self.name} ({self.admin})"
