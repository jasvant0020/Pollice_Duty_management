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
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
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

    @property
    def photo_url(self):
        if self.profile_photo and hasattr(self.profile_photo, 'url'):
            return self.profile_photo.url
        return '/media/default_dp/default.png'

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

    #geofence applied
    ended_at = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    radius = models.IntegerField(default=100)  # meters
    geo_enabled = models.BooleanField(default=False)
    vvip_lat = models.FloatField(null=True, blank=True)
    vvip_lng = models.FloatField(null=True, blank=True)

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


class DutyAttendance(models.Model):
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "field_staff"},
        related_name="duty_attendance"
    )

    duty = models.ForeignKey(
        VVIPDuty,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    is_inside = models.BooleanField(default=False)

    last_location_lat = models.FloatField(null=True, blank=True)
    last_location_lng = models.FloatField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("staff", "duty")

    def __str__(self):
        return f"{self.staff} - {self.duty}"




from django.db.models import Max    
class FieldStaffRequest(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requests'
    )

    # USER BASED REQUEST NUMBER
    request_number = models.PositiveIntegerField(null=True, blank=True,editable=False)

    subject = models.CharField(max_length=255)
    message = models.TextField()

    submitted_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    is_notified = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('staff', 'request_number')
        ordering = ['-submitted_at']

    def save(self, *args, **kwargs):

        if not self.request_number:

            last_request = FieldStaffRequest.objects.filter(
                staff=self.staff
            ).aggregate(Max('request_number'))

            last_number = last_request['request_number__max'] or 0

            self.request_number = last_number + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Request {self.request_number} - {self.staff.username}"


class VVIPRequest(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    vvip = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vvip_requests'
    )

    receiver = models.ForeignKey(   # 🔥 NEW (admin or munsi)
        User,
        on_delete=models.CASCADE,
        related_name='received_vvip_requests'
    )

    request_number = models.PositiveIntegerField(null=True, blank=True, editable=False)

    subject = models.CharField(max_length=255)
    message = models.TextField()

    submitted_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('vvip', 'request_number')
        ordering = ['-submitted_at']

    def save(self, *args, **kwargs):

        if not self.request_number:
            last_request = VVIPRequest.objects.filter(
                vvip=self.vvip
            ).aggregate(Max('request_number'))

            last_number = last_request['request_number__max'] or 0
            self.request_number = last_number + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Request {self.request_number} - {self.vvip.username}"
    


    

class FCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fcm_tokens")

    token = models.TextField(unique=True)

    device_name = models.CharField(max_length=255, blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)

    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

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


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ("request_status", "Request Status"),
        ("request", "Staff Request"),
        ("duty_assigned", "Duty Assigned"),
        ("duty_ended", "Duty Ended"),
        ("system_alert", "System Alert"),
        ("centralized", "Centralized Notification"),
    )

    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("critical", "Critical"),
    )

    # 🔹 Sender
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications_sent",
        db_index=True
    )

    # 🔹 Receiver (previously 'user')
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="centralized_notifications_receive",
        null=True,
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

    # 🔹 Generic relation (link to request/duty/etc)
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

    # 🔹 Dynamic metadata
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Extra dynamic notification data"
    )

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_archived = models.BooleanField(default=False)

    # 🔹 Soft delete
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["receiver", "is_read"]),
            models.Index(fields=["receiver", "created_at"]),
            models.Index(fields=["receiver", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.notification_type})"


from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CentralizedNotifyLog(models.Model):

    NOTIFY_TYPE = (
        ("normal", "Normal"),
        ("sos", "SOS")
    )

    SCOPE_TYPE = (
        ("staff", "All Dedicated Staff"),
        ("admin", "All Dedicated Admin"),
        ("specific", "Specific Person")
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="centralized_notifications_sent"
    )

    notify_type = models.CharField(
        max_length=20,
        choices=NOTIFY_TYPE
    )

    scope = models.CharField(
        max_length=20,
        choices=SCOPE_TYPE
    )

    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(
        max_length=255
    )

    message = models.TextField()

    # ⭐ NEW FIELD (store all recipients)
    recipients = models.JSONField(
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.scope} ({self.notify_type})"
    

class VerifyEmailOtp(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_otps"
    )

    otp = models.CharField(max_length=6)

    created_by = models.ForeignKey(   # 🔥 who generated OTP
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_email_otps"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_verified = models.BooleanField(default=False)

    # 🔐 SECURITY FIELDS
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