from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


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
    rank = models.CharField(max_length=50, null=True, blank=True)
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



# class SecurityCategory(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     total_personnel = models.PositiveIntegerField()
#     personnel_by_rank = models.JSONField(default=dict, blank=True)  # e.g., {"SP": 2, "Addl SP": 3}

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name
