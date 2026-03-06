from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.conf import settings
import uuid
from django.utils import timezone

class User(AbstractUser):

    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('master_admin', 'Master Admin'),
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('gd_munsi', 'GD Munsi'),
        ('field_staff', 'Field Staff'),
        ('vvip', 'VVIP'),
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

    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        null=True,
        blank=True
    )

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
        related_name="gd_munsi_admin", #this ensure that "GD Munsi and VVIP belongs to Admin"
        limit_choices_to={'role': 'admin'}
    )

    # Field staff → ONE GD
    gd_munsi = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="field_staffs", #this ensure that "field_staffs belongs to gd_munsi"
        limit_choices_to={'role': 'gd_munsi'}
    )

    # category → VVIP
    category = models.ForeignKey(
        "SecurityCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vvips"
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


class VVIPDuty(models.Model):

    batch_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )

    vvip = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "vvip"},
        related_name="duties"
    )

    category = models.ForeignKey(
        SecurityCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duties"
    )

    field_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "field_staff"},
        related_name="assigned_duties"
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="gd_assigned_duties",
        limit_choices_to={"role": "gd_munsi"}
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    # 🔥 NEW FIELDS (SAFE ADDITION)

    duty_place = models.CharField(max_length=255, null=True, blank=True)

    start_datetime = models.DateTimeField(null=True, blank=True)

    end_datetime = models.DateTimeField(null=True, blank=True)

    vehicle = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    DUTY_TYPE_CHOICES = [
        ("static", "Static"),
        ("escort", "Escort"),
        ("event", "Event"),
    ]

    duty_type = models.CharField(
        max_length=20,
        choices=DUTY_TYPE_CHOICES,
        default="static"
    )

    special_instructions = models.TextField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    end_reason = models.TextField(null=True, blank=True)

    ended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ended_duties"
    )

    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['vvip', 'field_staff'],
                condition=Q(is_active=True),
                name='unique_active_vvip_fieldstaff'
            )
        ]

    def __str__(self):
        return f"{self.vvip} → {self.field_staff} ({self.category})"
    
class FieldStaffRequest(models.Model):
        STATUS_CHOICES = (
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        )

        staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
        subject = models.CharField(max_length=255)
        message = models.TextField()
        submitted_at = models.DateTimeField(auto_now_add=True)
        status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

        is_notified = models.BooleanField(default=False)
        notified_at = models.DateTimeField(null=True, blank=True)

        def __str__(self):
            return f"{self.subject} ({self.staff.username})"
        

class FCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fcm_tokens")

    token = models.TextField(unique=True)

    device_name = models.CharField(max_length=255, blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)

    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
    
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import random


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    # 🔐 NEW FIELDS
    attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def remaining_attempts(self):
        return max(0, 5 - self.attempts)

    def lock(self):
        self.is_locked = True
        self.locked_until = timezone.now() + timedelta(minutes=10)
        self.save()

    def unlock_if_time_passed(self):
        if self.is_locked and self.locked_until and timezone.now() > self.locked_until:
            self.is_locked = False
            self.attempts = 0
            self.locked_until = None
            self.save()

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f"{self.user.email} - {self.otp}"


# from django.db import models
# from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ("request_status", "Request Status"),
        ("duty_assigned", "Duty Assigned"),
        ("duty_ended", "Duty Ended"),
        ("system_alert", "System Alert"),
    )

    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("critical", "Critical"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="normal"
    )

    # Generic relation (BEST PRACTICE)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    object_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    related_object = GenericForeignKey(
        "content_type",
        "object_id"
    )

    is_read = models.BooleanField(default=False)

    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.notification_type}"