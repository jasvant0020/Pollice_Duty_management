from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Hierarchy', {'fields': ('role', 'created_by', 'admin', 'gd_munsi')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'role', 'created_by', 'admin', 'gd_munsi',
                'is_staff', 'is_active'
            )
        }),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(User, CustomUserAdmin)







from .models import *

# ================= SECURITY CATEGORY =================
@admin.register(SecurityCategory)
class SecurityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', 'total_personnel')
    search_fields = ('name',)


# ================= VVIP DUTY =================
@admin.register(VVIPDuty)
class VVIPDutyAdmin(admin.ModelAdmin):
    list_display = (
        'vvip', 'field_staff', 'category',
        'duty_type', 'start_datetime',
        'end_datetime', 'is_active'
    )

    list_filter = ('duty_type', 'is_active', 'category')
    search_fields = ('vvip__username', 'field_staff__username')
    readonly_fields = ('batch_id', 'assigned_at')


# ================= ATTENDANCE =================
@admin.register(DutyAttendance)
class DutyAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'staff', 'duty',
        'check_in_time', 'check_out_time',
        'is_inside'
    )
    search_fields = ('staff__username',)


# ================= FIELD STAFF REQUEST =================
@admin.register(FieldStaffRequest)
class FieldStaffRequestAdmin(admin.ModelAdmin):
    list_display = ('staff', 'request_number', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('staff__username', 'subject')


# ================= VVIP REQUEST =================
@admin.register(VVIPRequest)
class VVIPRequestAdmin(admin.ModelAdmin):
    list_display = ('vvip', 'receiver', 'request_number', 'status')
    list_filter = ('status',)


# ================= NOTIFICATION =================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'sender', 'receiver',
        'notification_type',
        'priority',
        'is_read',
        'created_at'
    )
    list_filter = ('notification_type', 'priority', 'is_read')


# ================= CENTRALIZED LOG =================
@admin.register(CentralizedNotifyLog)
class CentralizedNotifyLogAdmin(admin.ModelAdmin):
    list_display = ('sender', 'scope', 'notify_type', 'created_at')


@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'browser', 'os', 'created_at','is_active')

    search_fields = (
        'user__username',
        'user__email',
        'device_name',
        'browser',
        'os',
        'token'
    )

    list_filter = ('browser', 'os', 'created_at','is_active')


# ================= SIMPLE MODELS =================
admin.site.register(PasswordResetOTP)
admin.site.register(VerifyEmailOtp)


# ================= HEADER =================
admin.site.site_header = "Police Duty Management"
admin.site.site_title = "Control Panel"
admin.site.index_title = "Admin Dashboard"