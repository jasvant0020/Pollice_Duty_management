# Create your views here.
from argparse import Action

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .models import User
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from app.models import User
from app.decorators import role_required
from django.db.models import Q
from app.utils.user_counts import get_admin_staff_counts, get_super_admin_dashboard_data, get_admin_dashboard_data
from app.utils import notification_service
from django.db.models import Count
from app.models import SecurityCategory,Notification,CentralizedNotifyLog
from app.utils.auth_utils import has_suspended_parent,ROLE_HIERARCHY,require_reset_session
from django.contrib.auth import update_session_auth_hash
from .models import User, VVIPDuty
from collections import defaultdict
from django.db import transaction   
from django.template.loader import render_to_string
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import fonts
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from .models import VVIPDuty
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone
from .models import FieldStaffRequest,VVIPRequest,VerifyEmailOtp
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from .models import FCMToken
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from app.firebase_service import send_push_notification






# Dummy data for testing frontend
POLICE_PERSONNEL = [
    {'name': 'Bhanu Kumar', 'category': 'Inspector', 'status': 'Available'},
    {'name': 'Rudra Singh', 'category': 'Constable', 'status': 'Assigned'},
    {'name': 'Raju Rajput', 'category': 'SP', 'status': 'Available'},
    {'name': 'Aman Singh', 'category': 'Constable', 'status': 'Assigned'},
    {'name': 'Aniket Jha', 'category': 'SP', 'status': 'Available'},
]

VVIP_PERSONS = [
    {'name': 'Mr. President', 'category': 'High', 'location': 'City Hall'},
    {'name': 'Ambassador Lee', 'category': 'Medium', 'location': 'Embassy'},
    {'name': 'Mr. President', 'category': 'High', 'location': 'Sansad'},
    {'name': 'CM Yogi', 'category': 'Medium', 'location': 'National Park'},
]

role = [
    {'role': 'GD Munsi'},
    {'role': 'User'}
]

police_rank = [
    {'police_rank': 'Director General of Police (DGP)'},
    {'police_rank': 'Additional Director General of Police (ADGP)'},
    {'police_rank': 'Inspector General of Police (IGP)'},
    {'police_rank': 'Deputy Inspector General of Police (DIG)'},
    {'police_rank': 'Superintendent of Police (SP)'},
    {'police_rank': 'Additional Superintendent of Police (Addl SP)'},
    {'police_rank': 'Deputy Superintendent of Police (DSP) / Assistant Commissioner of Police (ACP)'},
    {'police_rank': 'Inspector'},  
    {'police_rank': 'Sub-Inspector (SI)'},
    {'police_rank': 'Assistant Sub-Inspector (ASI)'},
    {'police_rank': 'Head Constable (HC)'},
    {'police_rank': 'Constable'}
]


category = [
    {'category': 'X Security'},
    {'category': 'Y Security'},
    {'category': 'Y+ Security'},
    {'category': 'Z Security'},
    {'category': 'Z+ Security'},
    {'category': 'SPG Security'},  # Special Protection Group (highest level, for PM of India)
    {'category':'other'}
]

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email not found!")
            return redirect("login")

        # 1️⃣ Block if any parent in hierarchy is suspended
        if has_suspended_parent(user_obj):
            messages.error(
                request,
                "Your administrator account is suspended. Access is temporarily disabled."
            )
            return redirect("login")

        # 2️⃣ Block if user himself is suspended
        if not user_obj.is_active:
            messages.error(
                request,
                "Your account has been suspended. Please contact your administrator."
            )
            return redirect("login")

        # 3️⃣ Authenticate
        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )

        if user is not None:
            login(request, user)

            if user.role == "developer":
                return redirect("admin:index")
            elif user.role in ["master_admin", "super_admin", "admin"]:
                return redirect("admin_dashboard")
            elif user.role == "gd_munsi":
                return redirect("munsi_dashboard")
            elif user.role == "field_staff":
                return redirect("user_profile")
            elif user.role == "vvip":
                return redirect("vvip_profile")

            messages.error(request, "Unknown role assigned!")
            return redirect("login")

        messages.error(request, "Invalid credentials")
        return redirect("login")

    return render(request, "login_panel/login.html")


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    messages.success(request,"you have been logged out successfully!")
    return redirect('login')



from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import PasswordResetOTP
from django.contrib.auth import get_user_model

User = get_user_model()


from django.utils import timezone
from datetime import timedelta

def forgot_password_view(request):

    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email not registered.")
            return redirect("forgot_password")

        # Get latest OTP record
        last_otp = PasswordResetOTP.objects.filter(
            user=user
        ).order_by("-created_at").first()

        if last_otp:

            # 🔓 Auto unlock if time passed
            last_otp.unlock_if_time_passed()

            # 🚫 BLOCK if locked
            if last_otp.is_locked:
                remaining_seconds = int(
                    (last_otp.locked_until - timezone.now()).total_seconds()
                )

                return render(request, "password_panel/forgot_password.html", {
                    "lock_remaining": remaining_seconds,
                    "lock_until": last_otp.locked_until.isoformat()
                })

            # 🔁 Cooldown 60 sec resend
            seconds_passed = (timezone.now() - last_otp.created_at).total_seconds()
            if seconds_passed < 60:
                remaining = int(60 - seconds_passed)
                messages.error(request, f"Wait {remaining} seconds before resending OTP.")
                return redirect("forgot_password")

        # ✅ Generate new OTP
        otp_code = PasswordResetOTP.generate_otp()

        PasswordResetOTP.objects.create(
            user=user,
            otp=otp_code
        )

        expiry_time = timezone.now() + timedelta(minutes=5)

        request.session.flush()
        request.session["reset_email"] = email
        request.session["otp_expiry"] = expiry_time.isoformat()
        request.session["otp_step"] = "verify"

        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP is: {otp_code}\nValid for 5 minutes.",
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "OTP sent successfully.")
        return redirect("verify_otp")

    return render(request, "password_panel/forgot_password.html")

def verify_otp_view(request):

    if request.session.get("otp_step") != "verify":
        return redirect("forgot_password")

    email = request.session.get("reset_email")
    expiry_time = request.session.get("otp_expiry")

    user = User.objects.get(email=email)

    otp_record = PasswordResetOTP.objects.filter(
        user=user,
        is_verified=False
    ).latest("created_at")

    # 🔓 Unlock automatically if time passed
    otp_record.unlock_if_time_passed()

    # 🚫 If locked
    if otp_record.is_locked:
        remaining_lock = int((otp_record.locked_until - timezone.now()).total_seconds())
        messages.error(request, f"Account locked. Try again in {remaining_lock // 60} minutes.")
        return redirect("forgot_password")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        # ❌ Wrong OTP
        if entered_otp != otp_record.otp:

            otp_record.attempts += 1
            otp_record.save()

            remaining = otp_record.remaining_attempts()

            if remaining <= 0:
                otp_record.lock()
                messages.error(request, "Too many wrong attempts. Locked for 10 minutes.")
                return redirect("forgot_password")

            messages.error(request, f"Invalid OTP. {remaining} attempts remaining.")
            return redirect("verify_otp")

        # ⏰ Expired
        if otp_record.is_expired():
            request.session.flush()
            messages.error(request, "OTP expired.")
            return redirect("forgot_password")

        # ✅ Correct OTP
        otp_record.is_verified = True
        otp_record.save()

        request.session["otp_step"] = "reset"
        return redirect("reset_password")

    return render(request, "password_panel/verify_otp.html", {
        "expiry_time": expiry_time,
        "remaining_attempts": otp_record.remaining_attempts()
    })

def reset_password_view(request):

    # 🚫 Block direct access
    if request.session.get("otp_step") != "reset":
        return redirect("forgot_password")

    email = request.session.get("reset_email")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password")

        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        # 🔐 Clear everything after success
        request.session.flush()

        messages.success(request, "Password reset successful.")
        return redirect("login")

    return render(request, "password_panel/reset_password.html")

@role_required(["gd_munsi"])
def police_list(request):
    context = {'police_personnel': POLICE_PERSONNEL}
    return render(request, 'GD_munsi_panel/police_list.html', context)

@role_required(["gd_munsi"])
def vvip_list(request):
    context = {'vvip_persons': VVIP_PERSONS}
    return render(request, 'GD_munsi_panel/vvip_list.html', context)

@role_required(["gd_munsi"])
def assign_duty(request):
    context = {
        'police_personnel': POLICE_PERSONNEL,
        'vvip_persons': VVIP_PERSONS
    }
    return render(request, 'GD_munsi_panel/assign_duty.html', context)

@role_required(["gd_munsi"])
def munsi_assign_duty(request):

    gd = request.user

    active_vvip_ids = VVIPDuty.objects.filter(
        is_active=True
    ).values_list("vvip_id", flat=True)

    vvips = User.objects.filter(
        role="vvip",
        admin=gd.admin
    ).exclude(id__in=active_vvip_ids)

    categories = SecurityCategory.objects.filter(admin=gd.admin)

    if request.method == "POST":

        from django.utils.dateparse import parse_datetime


        vvip_id = request.POST.get("vvip")

        # 🔍 Get previous assignment count per staff for this VVIP
        previous_assignments = (
            VVIPDuty.objects
            .filter(vvip_id=vvip_id)
            .values(
                "field_staff__id",
                "field_staff__first_name",
                "field_staff__last_name",
                "field_staff__rank"
            )
            .annotate(assign_count=Count("id"))
            .order_by("-assign_count")
        )



        category_id = request.POST.get("category")
        duty_place = request.POST.get("duty_place")
        start_datetime = parse_datetime(request.POST.get("start_datetime"))
        end_datetime = parse_datetime(request.POST.get("end_datetime"))

        # ❗ Check if datetime parsed properly
        if not start_datetime or not end_datetime:
            messages.error(request, "Invalid date/time format.")
            return redirect("munsi_assign_duty")

        # 🔥 Convert to aware datetime (IMPORTANT if USE_TZ=True)
        if timezone.is_naive(start_datetime):
            start_datetime = timezone.make_aware(start_datetime)

        if timezone.is_naive(end_datetime):
            end_datetime = timezone.make_aware(end_datetime)

        now = timezone.now()

        # 🚫 Block past start time
        if start_datetime < now:
            messages.error(request, "Start time cannot be in the past.")
            return redirect("munsi_assign_duty")

        # 🚫 Block past end time
        if end_datetime < now:
            messages.error(request, "End time cannot be in the past.")
            return redirect("munsi_assign_duty")

        # 🚫 End must be after start
        if end_datetime <= start_datetime:
            messages.error(request, "End time must be after start time.")
            return redirect("munsi_assign_duty")

        vehicle = request.POST.get("vehicle") or None

        latitude = request.POST.get("latitude") or None
        longitude = request.POST.get("longitude") or None

        if latitude:
            latitude = float(latitude)
        if longitude:
            longitude = float(longitude)
            
        radius = request.POST.get("radius") or 100
        geo_enabled = request.POST.get("geo_enabled") == "on"
        
        duty_type = request.POST.get("duty_type") or "static"
        if duty_type == "other":
            duty_type = request.POST.get("custom_duty_type")

        special_instructions = request.POST.get("special_instructions")

        confirm_partial = request.POST.get("confirm_partial")
        confirm_reassign = request.POST.get("confirm_reassign")


        # if end_datetime <= start_datetime:
        #     messages.error(request, "End time must be after start time.")
        #     return redirect("munsi_assign_duty")


        if not vvip_id or not category_id:
            messages.error(request, "Please select VVIP and Category.")
            return redirect("munsi_assign_duty")

        vvip = get_object_or_404(User, id=vvip_id, role="vvip")
        category = get_object_or_404(SecurityCategory, id=category_id)

        required_rank_data = category.personnel_by_rank or {}

        if not required_rank_data:
            messages.error(request, "No rank structure defined in this category.")
            return redirect("munsi_assign_duty")

        # 🔥 Exclude staff already on ACTIVE duty (any VVIP)
        already_active_staff = VVIPDuty.objects.filter(
            is_active=True
        ).values_list("field_staff_id", flat=True)

        field_staffs = User.objects.filter(
            role="field_staff",
            gd_munsi=gd
        ).exclude(id__in=already_active_staff)

        assignment_plan = {}
        shortage_messages = []
        total_required = 0
        total_assignable = 0

        # 🔎 RANK-WISE CHECKING
        for rank, required_count in required_rank_data.items():

            required_count = int(required_count)  # safety
            total_required += required_count

            available_rank_staff = field_staffs.filter(rank=rank)

            # 🔹 Staff who NEVER served this VVIP before
            never_assigned_staff = available_rank_staff.exclude(
                id__in=VVIPDuty.objects.filter(
                    vvip_id=vvip_id
                ).values_list("field_staff_id", flat=True)
            )

            never_count = never_assigned_staff.count()
            available_count = available_rank_staff.count()

            # Prefer new staff first
            assignable = min(required_count, available_count)

            total_assignable += assignable

            assignment_plan[rank] = {
                "required": required_count,
                "available": available_count,
                "never_queryset": never_assigned_staff,
                "full_queryset": available_rank_staff,
                "never_count": never_count,
            }


            shortage_messages.append(
                f"{rank}: Required {required_count}, Available {available_count}"
            )

        # 🚨 Shortage detected
        # 🚨 CASE 1 — Nothing can be assigned at all
        if total_assignable == 0:
            return render(request, "GD_munsi_panel/munsi_assign_duty.html", {
                "vvips": vvips,
                "categories": categories,
                "confirm_partial": True,
                "selected_vvip": int(vvip_id),
                "selected_category": int(category_id),
                "shortage_messages": shortage_messages,
                "total_required": total_required,
                "total_assignable": total_assignable,
                "assignment_blocked": True,   # special flag
            })


        # 🚨 CASE 2 — Partial shortage
        if shortage_messages and not confirm_partial:

            # 🚨 CASE 3 — Unique staff not enough, ask before reassigning
            reassign_needed = False

            for rank, data in assignment_plan.items():
                if data["available"] > 0 and data["never_count"] < data["available"]:
                    reassign_needed = True
                    break

            if reassign_needed and not confirm_reassign:
                return render(request, "GD_munsi_panel/munsi_assign_duty.html", {
                    "vvips": vvips,
                    "categories": categories,
                    "confirm_reassign": True,
                    "previous_assignments": previous_assignments,
                    "selected_vvip": int(vvip_id),
                    "selected_category": int(category_id),
                    "shortage_messages": shortage_messages,
                    "total_required": total_required,
                    "total_assignable": total_assignable,
                })


            return render(request, "GD_munsi_panel/munsi_assign_duty.html", {
                "vvips": vvips,
                "categories": categories,
                "confirm_partial": True,
                "selected_vvip": int(vvip_id),
                "selected_category": int(category_id),
                "shortage_messages": shortage_messages,
                "total_required": total_required,
                "total_assignable": total_assignable,
            })



        # ✅ FINAL ASSIGNMENT (Atomic Safe)
        assigned_count = 0

        with transaction.atomic():

            batch_id = uuid.uuid4()   # 🔥 ONE batch for this full assignment

            for rank, data in assignment_plan.items():

                required = data["required"]
                required = data["required"]

                # First take never assigned staff
                never_staff = data["never_queryset"][:required]
                remaining_needed = required - never_staff.count()

                if remaining_needed > 0:
                    # Allow reassignment only if confirmed
                    reassign_staff = data["full_queryset"].exclude(
                        id__in=never_staff.values_list("id", flat=True)
                    )[:remaining_needed]

                    final_staff_queryset = list(never_staff) + list(reassign_staff)
                else:
                    final_staff_queryset = list(never_staff)

                channel_layer = get_channel_layer()

                for staff in final_staff_queryset:


                    exists = VVIPDuty.objects.filter(
                        vvip=vvip,
                        field_staff=staff,
                        is_active=True
                    ).exists()

                    if not exists:
                        VVIPDuty.objects.create(
                            vvip=vvip,
                            category=category,
                            field_staff=staff,
                            assigned_by=gd,
                            duty_place=duty_place,
                            start_datetime=start_datetime,
                            end_datetime=end_datetime,
                            vehicle=vehicle,
                            duty_type=duty_type,
                            special_instructions=special_instructions,
                            is_active=True,
                            batch_id=batch_id,   # 🔥 CRITICAL LINE

                            latitude=latitude,
                            longitude=longitude,
                            radius=radius,
                            geo_enabled=geo_enabled
                        )

                        assigned_count += 1
                    
                    from django.urls import reverse

                    # 🔔 Create In-App Notification
                    notification = Notification.objects.create(
                        receiver=staff,
                        sender=request.user,
                        title="New VVIP Duty Assigned",
                        message=f"You have been assigned VVIP duty for {vvip.get_full_name()} at {duty_place}.",
                        notification_type="duty_assigned",
                        priority="high",
                        metadata={
                            "vvip_name": vvip.get_full_name(),
                            "duty_place": duty_place,
                            "start_datetime": start_datetime.isoformat(),
                            "end_datetime": end_datetime.isoformat(),
                            "batch_id": str(batch_id)
                        }
                    )

                    # 🔔 WebSocket Real-Time Notification
                    async_to_sync(channel_layer.group_send)(
                        f"user_{staff.id}",
                        {
                            "type": "send_status_update",
                            "data": {
                                "title": notification.title,
                                "message": notification.message,
                                "notification_id": notification.id
                            }
                        }
                    )
                    
                    from django.urls import reverse
                    # 🔥 Firebase Push Notification
                    send_push_notification(
                        user=staff,
                        title="New Duty Assigned",
                        body=f"You have been assigned VVIP duty.",
                        id=str(batch_id),
                        url=reverse("user_assign_duty"),
                        sender=gd,
                        notification_type="duty"
                    )

        # ✅ SUCCESS MESSAGE
        if shortage_messages:
            messages.success(
                request,
                f"Partial assignment completed ({assigned_count}/{total_required})."
            )
        else:
            messages.success(
                request,
                f"Duty assigned successfully ({assigned_count} personnel deployed)."
            )

        return redirect("munsi_active_duty")

    return render(request, "GD_munsi_panel/munsi_assign_duty.html", {
        "vvips": vvips,
        "categories": categories
    })


@role_required(["gd_munsi"])
def munsi_edit_vvip_duty(request, batch_id):

    gd = request.user

    duties = VVIPDuty.objects.filter(
        batch_id=batch_id,
        assigned_by=gd,
        is_active=True
    )

    if not duties.exists():
        messages.error(request, "No active duty found for this batch.")
        return redirect("munsi_active_duty")

    duty = duties.first()  # common data for batch

    if request.method == "POST":

        from django.utils.dateparse import parse_datetime

        duty_place = request.POST.get("duty_place")
        vehicle = request.POST.get("vehicle")

        start_datetime = parse_datetime(request.POST.get("start_datetime"))
        end_datetime = parse_datetime(request.POST.get("end_datetime"))

        special_instructions = request.POST.get("special_instructions")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        radius = request.POST.get("radius") or 100

        # ❗ Validate datetime
        if not start_datetime or not end_datetime:
            messages.error(request, "Invalid date/time format.")
            return redirect("munsi_active_duty")

        # 🔥 Make timezone aware
        if timezone.is_naive(start_datetime):
            start_datetime = timezone.make_aware(start_datetime)

        if timezone.is_naive(end_datetime):
            end_datetime = timezone.make_aware(end_datetime)

        now = timezone.now()

        # 🚫 Validation rules (same as assign)
        if start_datetime < now:
            messages.error(request, "Start time cannot be in the past.")
            return redirect("munsi_active_duty")

        if end_datetime < now:
            messages.error(request, "End time cannot be in the past.")
            return redirect("munsi_active_duty")

        if end_datetime <= start_datetime:
            messages.error(request, "End time must be after start time.")
            return redirect("munsi_active_duty")

        # ✅ UPDATE ALL DUTIES IN BATCH
        duties.update(
            duty_place=duty_place,
            vehicle=vehicle,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            special_instructions=special_instructions,
            latitude=latitude,
            longitude=longitude,
            radius=radius
        )

        messages.success(request, "Duty updated successfully.")

        return redirect("munsi_active_duty")

    return redirect("munsi_active_duty")

@role_required(["gd_munsi"])
def munsi_reassign_duty(request, batch_id):

    gd = request.user

    duties = VVIPDuty.objects.filter(
        batch_id=batch_id,
        assigned_by=gd
    ).select_related("vvip", "category")

    if not duties.exists():
        messages.error(request, "Invalid batch.")
        return redirect("munsi_active_duty")

    duty_sample = duties.first()
    category = duty_sample.category
    vvip = duty_sample.vvip

    required_rank_data = category.personnel_by_rank or {}

    # 🔥 CURRENT ACTIVE STAFF (remaining after removal)
    active_staff_ids = duties.filter(is_active=True).values_list("field_staff_id", flat=True)

    # 🔥 Already active globally (avoid conflict)
    globally_active_staff = VVIPDuty.objects.filter(
        is_active=True
    ).values_list("field_staff_id", flat=True)

    available_staff = User.objects.filter(
        role="field_staff",
        gd_munsi=gd
    ).exclude(id__in=globally_active_staff)

    assignment_needed = {}

    for rank, required_count in required_rank_data.items():
        current_count = duties.filter(
            is_active=True,
            field_staff__rank=rank
        ).count()

        shortage = int(required_count) - current_count

        if shortage > 0:
            assignment_needed[rank] = {
                "required": required_count,
                "current": current_count,
                "shortage": shortage,
                "available_staff": available_staff.filter(rank=rank)
            }

    if request.method == "POST":

        selected_ids = request.POST.getlist("selected_staff")

        with transaction.atomic():

            for rank, data in assignment_needed.items():

                # 🔵 MANUAL MODE
                if selected_ids:
                    staff_queryset = User.objects.filter(
                        id__in=selected_ids,
                        rank=rank
                    )[:data["shortage"]]

                # 🟢 AUTO MODE
                else:
                    staff_queryset = data["available_staff"][:data["shortage"]]

                for staff in staff_queryset:
                    VVIPDuty.objects.create(
                        vvip=vvip,
                        category=category,
                        field_staff=staff,
                        assigned_by=gd,
                        duty_place=duty_sample.duty_place,
                        start_datetime=timezone.now(),
                        end_datetime=duty_sample.end_datetime,
                        vehicle=duty_sample.vehicle,
                        duty_type=duty_sample.duty_type,
                        special_instructions=duty_sample.special_instructions,
                        is_active=True,
                        batch_id=batch_id
                    )
        
        messages.success(request, "Replacement staff assigned successfully.")
        return redirect("munsi_active_duty")
    
    has_available_staff = any(
            data["available_staff"].exists()
            for data in assignment_needed.values()
        )
        
    return render(request, "GD_munsi_panel/munsi_reassign_duty.html", {
        "assignment_needed": assignment_needed,
        "vvip": vvip,
        "has_available_staff": has_available_staff
    })



@role_required(["gd_munsi"])
def munsi_dashboard(request):

    gd = request.user

    duties = VVIPDuty.objects.filter(
        assigned_by=gd,
        is_active=True
    ).select_related("vvip", "field_staff", "category")
    # ✅ Count UNIQUE VVIP only
    active_vvip_count = duties.values("vvip").distinct().count()

    return render(request, "GD_munsi_panel/munsi_dashboard.html", {
        "active_duty_count": active_vvip_count,
    })

@role_required(["gd_munsi"])
def munsi_active_duty(request):

    gd = request.user

    duties = VVIPDuty.objects.filter(
        assigned_by=gd,
        is_active=True
    ).select_related("vvip", "field_staff", "category")

    grouped_duties = defaultdict(list)

    for duty in duties:
        grouped_duties[duty.batch_id].append(duty)

    # 🔥 ADD THIS BLOCK
    enriched_grouped_duties = {}

    for batch_id, duty_list in grouped_duties.items():

        category = duty_list[0].category
        personnel = category.personnel_by_rank or {}

        total_required = sum(int(v) for v in personnel.values())
        current_count = len(duty_list)

        enriched_grouped_duties[batch_id] = {
            "duties": duty_list,
            "total_required": total_required,
            "current_count": current_count,
            "has_shortage": current_count < total_required
        }

    return render(request, "GD_munsi_panel/munsi_active_duty.html", {
        "grouped_duties": enriched_grouped_duties,
        "active_duty_count": len(grouped_duties),
    })

@role_required(["gd_munsi"])
def munsi_previous_duties(request):

    gd = request.user

    duties = VVIPDuty.objects.filter(
        assigned_by=gd,
        is_active=False
    ).select_related("vvip", "field_staff", "category")

    grouped_duties = defaultdict(list)

    for duty in duties:
        grouped_duties[duty.batch_id].append(duty)

    return render(request, "GD_munsi_panel/munsi_previous_duties.html", {
        "grouped_duties": dict(grouped_duties)
    })


@role_required(["gd_munsi"])
def munsi_deactivate_duty_individual(request, duty_id):

    gd = request.user

    if request.method == "POST":

        reason = request.POST.get("end_reason")

        if not reason:
            messages.error(request, "Please provide a reason for ending duty.")
            return redirect("munsi_active_duty")

        try:

            duty = VVIPDuty.objects.get(
                id=duty_id,
                assigned_by=gd,
                is_active=True
            )

            staff = duty.field_staff

            # 🔹 End only THIS duty
            duty.is_active = False
            duty.end_reason = reason
            duty.ended_by = gd
            duty.ended_at = timezone.now()
            duty.end_datetime = timezone.now()
            duty.save()

            # 🔔 Create notification
            notification = Notification.objects.create(
                receiver=staff,
                sender=request.user,
                title="VVIP Duty Ended",
                message=f"Your duty for {duty.vvip.get_full_name()} has been ended.",
                notification_type="duty_ended",
                priority="high",
                metadata={
                    "vvip_name": duty.vvip.get_full_name(),
                    "batch_id": str(duty.batch_id),
                    "reason": reason
                }
            )

            # 🔴 WebSocket
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"user_{staff.id}",
                {
                    "type": "send_status_update",
                    "data": {
                        "title": notification.title,
                        "message": notification.message,
                        "notification_id": notification.id
                    }
                }
            )

            # 🔥 Firebase push
            try:
                send_push_notification(
                    user=staff,
                    title="Duty Ended",
                    body=f"Your duty for {duty.vvip.get_full_name()} has been ended.",
                    id=str(duty.batch_id),
                    url=reverse("user_assign_duty"),
                    sender=gd,
                    notification_type="duty"
                )
            except Exception as e:
                print("Push notification error:", e)

            messages.success(request, "Individual duty ended successfully!")

        except VVIPDuty.DoesNotExist:
            messages.error(request, "Duty not found or already inactive.")

    return redirect("munsi_active_duty")



@role_required(["gd_munsi"])
def munsi_end_vvip_duty(request, batch_id):

    gd = request.user

    if request.method == "POST":

        reason = request.POST.get("end_reason")

        if not reason:
            messages.error(request, "Please provide a reason for ending duty.")
            return redirect("munsi_active_duty")

        duties = VVIPDuty.objects.filter(
            batch_id=batch_id,
            assigned_by=gd,
            is_active=True
        )

        if duties.exists():

            # ✅ Evaluate staff BEFORE update
            staff_users = [d.field_staff for d in duties.select_related("field_staff")]

            # 🔹 End all duties in batch
            duties.update(
                is_active=False,
                end_reason=reason,
                ended_by=gd,
                ended_at=timezone.now(),
                end_datetime=timezone.now()
            )

            # 🔔 WebSocket channel layer
            channel_layer = get_channel_layer()

            # 🔔 Send notifications
            for staff in staff_users:

                notification = Notification.objects.create(
                    receiver=staff,
                    sender=request.user,
                    title="VVIP Duty Ended",
                    message="Your VVIP duty has been ended.",
                    notification_type="duty_ended",
                    priority="high",
                    metadata={
                        "batch_id": str(batch_id),
                        "reason": reason
                    }
                )

                # 🔴 WebSocket real-time notification
                async_to_sync(channel_layer.group_send)(
                    f"user_{staff.id}",
                    {
                        "type": "send_status_update",
                        "data": {
                            "title": notification.title,
                            "message": notification.message,
                            "notification_id": notification.id
                        }
                    }
                )

                # 🔥 Firebase push
                try:
                    send_push_notification(
                        user=staff,
                        title="Duty Ended",
                        body="Your VVIP duty has been ended.",
                        id=str(batch_id),
                        url=reverse("user_assign_duty"),
                        sender=gd,
                        notification_type="duty"
                    )
                except Exception as e:
                    print("Push notification error:", e)

            messages.success(request, "Duty batch ended successfully.")

        else:
            messages.warning(request, "No active duties found.")

    return redirect("munsi_active_duty")



@role_required(["gd_munsi"])
def munsi_vvip_duty_print(request, batch_id):

    duties = VVIPDuty.objects.filter(
        batch_id=batch_id,
        is_active=True
    ).select_related(
        "vvip",
        "field_staff",
        "category",
        "assigned_by"
    )

    duty = duties.first()

    return render(request, "GD_munsi_panel/vvip_duty_print.html", {
        "vvip": duty.vvip if duty else None,
        "duties": duties,
        "duty": duty,
        "total_staff": duties.count()
    })



@role_required(["gd_munsi"])
def munsi_profile(request):
    
    return render(request, 'GD_munsi_panel/munsi_profile.html')

@role_required(["gd_munsi"])
def edit_munsi_profile(request):

    user = request.user   # Logged-in munshi

    if request.method == "POST":
        # Get form data
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")

        # 🔴 Email uniqueness check
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "Email already in use.")
                return redirect("edit_munsi_profile")
            
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Update basic fields
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = email
        user.phone = phone

        # Profile photo update
        # REMOVE PHOTO FIRST
        if request.POST.get("remove_photo") == "1":
            if user.profile_photo:
                user.profile_photo.delete(save=False)
            user.profile_photo = None

        # THEN HANDLE NEW UPLOAD
        elif request.FILES.get("profile_photo"):
            user.profile_photo = request.FILES.get("profile_photo")

        # Password change (only if provided)
        if password:
            if password == confirm_password:
                user.set_password(password)
                update_session_auth_hash(request, user)  # Keep user logged in
            else:
                messages.error(request, "Passwords do not match!")
                return redirect("edit_munsi_profile")

        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("munsi_profile")  # change if your profile url name is different

    return render(request, "GD_munsi_panel/edit_munsi_profile.html", {
        "user": user
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from .models import FieldStaffRequest


@role_required(["gd_munsi"])
def munsi_field_staff_requests(request):

    # 🔐 Only show requests of staff assigned to THIS GD Munsi
    base_queryset = FieldStaffRequest.objects.filter(
        staff__gd_munsi=request.user
    )

    pending_list = base_queryset.filter(
        status="pending"
    ).order_by('-submitted_at')

    approved_list = base_queryset.filter(
        status="approved"
    ).order_by('-submitted_at')

    rejected_list = base_queryset.filter(
        status="rejected"
    ).order_by('-submitted_at')

    # Pagination
    pending_paginator = Paginator(pending_list, 10)
    approved_paginator = Paginator(approved_list, 10)
    rejected_paginator = Paginator(rejected_list, 10)

    pending_page = request.GET.get('pending_page')
    approved_page = request.GET.get('approved_page')
    rejected_page = request.GET.get('rejected_page')

    context = {
        "pending_requests": pending_paginator.get_page(pending_page),
        "approved_requests": approved_paginator.get_page(approved_page),
        "rejected_requests": rejected_paginator.get_page(rejected_page),
    }

    return render(request, "GD_munsi_panel/munsi_field_staff_requests.html", context)


from django.urls import reverse
@role_required(["gd_munsi"])
def munsi_approve_request(request, req_id):

    req = get_object_or_404(
        FieldStaffRequest,
        id=req_id,
        staff__gd_munsi=request.user
    )

    req.status = "approved"
    req.notified_at = timezone.now()
    req.save()

    # 🔔 Create In-App Notification
    notification = Notification.objects.create(
        receiver=req.staff,
        sender=request.user,
        title="Request Approved",
        message=f"Your request (request id: {req.request_number}) has been approved.",
        notification_type="request_status",
        priority="normal",
        metadata={
            "note": "For more details visit Request History"
        }
    )

    # 🔔 Send websocket event
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"user_{req.staff.id}",
        {
            "type": "send_status_update",
            "data": {
                "title": notification.title,
                "message": notification.message,
            }
        }
    )

    # 🔥 Firebase Push Notification
    send_push_notification(
        id=req.request_number ,
        user=req.staff,
        title="Request Approved",
        body=req.subject,
        url=reverse("centrelize_Notifications"),
        notification_type="status"
    )

    return redirect("munsi_field_staff_requests")


@role_required(["gd_munsi"])
def munsi_reject_request(request, req_id):

    req = get_object_or_404(
        FieldStaffRequest,
        id=req_id,
        staff__gd_munsi=request.user
    )

    req.status = "rejected"
    req.notified_at = timezone.now()
    req.save()

    # 🔔 Create In-App Notification
    notification = Notification.objects.create(
        receiver=req.staff,
        sender=request.user,
        title="Request Rejected",
        message=f"Your request (request id: {req.request_number}) has been approved.",
        notification_type="request_status",
        priority="normal",
        metadata={
            "note": "For more details visit Request History"
        }
    )

    # 🔔 Send websocket event
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"user_{req.staff.id}",
        {
            "type": "send_status_update",
            "data": {
                "title": notification.title,
                "message": notification.message,
            }
        }
    )

    # 🔥 Firebase Push Notification
    send_push_notification(
        id=req.request_number ,
        user=req.staff,
        title="Request Rejected",
        body=req.subject,
        url=reverse("centrelize_Notifications"),
        notification_type="status"
    )

    return redirect("munsi_field_staff_requests")


#------ Custom Admin Panel Views ------
@role_required(["admin", "master_admin", "super_admin"])
def admin_dashboard(request):
    user = request.user

    super_admin_data = []
    admin_data = []

    # ✅ ADMIN LOGIC
    active_duty = 0

    if user.role == "admin":
        active_duty = VVIPDuty.objects.filter(
            assigned_by__role="gd_munsi",
            assigned_by__admin=user,
            is_active=True
        ).values("vvip").distinct().count()

    # ✅ MASTER ADMIN
    elif user.role == "master_admin":
        super_admin_data = get_super_admin_dashboard_data(user)

    # ✅ SUPER ADMIN
    elif user.role == "super_admin":
        admin_data = get_admin_dashboard_data(user)

    context = {
        **get_admin_staff_counts(user),
        "active_duty": active_duty,  # ✅ override correct value
        "super_admin_data": super_admin_data,
        "admin_data": admin_data,
    }

    return render(request, "admin_panel/admin_dashboard.html", context)

@role_required(["admin","master_admin","super_admin"])
def profile(request):
    return render(request, "admin_panel/profile.html")

@role_required(["admin","master_admin","super_admin"])
def edit_profile(request):
    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.phone = request.POST.get("phone")

        # EMAIL (check duplicate)
        new_email = request.POST.get("email")
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                messages.error(request, "Email already in use.")
                return redirect("edit_profile")
            user.email = new_email
            user.username = new_email  # if email-based login

        # PROFILE PHOTO
        # REMOVE PHOTO FIRST
        if request.POST.get("remove_photo") == "1":
            if user.profile_photo:
                user.profile_photo.delete(save=False)
            user.profile_photo = None

        # THEN HANDLE NEW UPLOAD
        elif request.FILES.get("profile_photo"):
            user.profile_photo = request.FILES.get("profile_photo")

        # PASSWORD CHANGE
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password or confirm_password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("edit_profile")
            user.set_password(password)

        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "admin_panel/edit_profile.html", {"user": user})

@role_required(["admin","master_admin","super_admin"])
def manage(request):
    return render(request, "admin_panel/manage.html")

@role_required(["admin","master_admin","super_admin"])
def police_hierarchy_table(request):
    admin_user = request.user

    # Fetch only ranks that exist in DB for this admin
    rank_qs = (
        User.objects
        .filter(
            admin=admin_user,      # only users belonging to this admin
            role="field_staff",    # ✅ only Field Staff
            rank__isnull=False
        )
        .exclude(rank="")          # exclude empty ranks
        .values("rank")            # group by rank
        .annotate(count=Count("id"))
        .order_by("-count")        # descending count
    )

    rank_status = []
    for r in rank_qs:
        count = r["count"]
        if count > 10:
            badge_color = "red"
            status = "High"
        elif count > 5:
            badge_color = "yellow"
            status = "Medium"
        else:
            badge_color = "green"
            status = "Low"

        rank_status.append({
            "rank": r["rank"],
            "count": count,
            "badge_color": badge_color,
            "status": status
        })


    context = {
        "rank_status": rank_status
    }

    return render(request, "admin_panel/police_hierarchy_table.html", context)


from django.core.paginator import Paginator  # ✅ ADD THIS
from django.db.models import Q

@role_required(["admin", "master_admin","super_admin"])
def manage_users(request):
    admin_user = request.user

    # 🔒 ORIGINAL LOGIC (UNCHANGED)
    officers = User.objects.filter(
        (
            Q(role="gd_munsi", admin=admin_user) |
            Q(role="field_staff", gd_munsi__admin=admin_user) |
            Q(created_by=admin_user)
        )
    ).exclude(role="vvip") \
     .distinct() \
     .order_by("role", "username")

    # 🔒 ORIGINAL FILTERING (UNCHANGED)
    suspended_officers = officers.filter(is_active=False)
    active_officers = officers.filter(is_active=True)
    gd_munsi = officers.filter(role="gd_munsi")
    field_staff = officers.filter(role="field_staff", is_active=True)

    # =======================
    # ✅ PAGINATION START
    # =======================

    # Field Staff Pagination
    field_paginator = Paginator(field_staff, 10)
    field_page = request.GET.get("users_page")
    field_staff = field_paginator.get_page(field_page)

    # All Staff Pagination
    all_paginator = Paginator(active_officers, 10)
    all_page = request.GET.get("page")
    officers = all_paginator.get_page(all_page)

    # GD Munshi Pagination
    gd_paginator = Paginator(gd_munsi, 10)
    gd_page = request.GET.get("gd_page")
    gd_munsi = gd_paginator.get_page(gd_page)

    # Suspended Pagination
    suspended_paginator = Paginator(suspended_officers, 10)
    suspended_page = request.GET.get("suspended_page")
    suspended_officers = suspended_paginator.get_page(suspended_page)

    # =======================
    # ✅ PAGINATION END
    # =======================

    return render(
        request,
        "admin_panel/manage_users.html",
        {
            "officers": officers,  # now paginated active users
            "active_officers": active_officers,  # untouched if needed elsewhere
            "suspended_officers": suspended_officers,
            "gd_munsi": gd_munsi,
            "field_staff": field_staff,
        }
    )


@role_required(["admin"])
def manage_vvip(request):
    vvips = User.objects.filter(
        role="vvip",
        admin=request.user
    ).select_related("category")

    active_vvips = vvips.filter(is_active=True)
    suspended_vvips = vvips.filter(is_active=False)

    return render(
        request,
        "admin_panel/manage_vvip.html",
        {
            "active_vvips": active_vvips,
            "suspended_vvips": suspended_vvips,
        }
    )


@role_required(["admin"])
def add_vvip(request):
    categories = SecurityCategory.objects.filter(admin=request.user)
    context = {
        "category": categories,
    }

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        gender = request.POST.get("gender")
        dob = request.POST.get("dob")

        # Rank handling
        rank = request.POST.get("rank")
        custom_rank = request.POST.get("custom_rank")
        if rank == "other":
            rank = custom_rank

        # Category handling
        category_id = request.POST.get("category")
        category_obj = SecurityCategory.objects.get(
            id=category_id,
            admin=request.user
        )

        # 🔴 Email uniqueness check
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered. Please use a different email.")
            return render(request, "admin_panel/add_vvip.html", context)
        
        # 🔴 Mobile validation
        if not phone or not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Enter a valid 10-digit phone number.")
            return render(request, "admin_panel/add_vvip.html", context)

        # 🔴 Unique mobile check (recommended)
        if User.objects.filter(phone=phone).exists():
            messages.error(request, "This mobile number is already registered.")
            return render(request, "admin_panel/add_vvip.html", context)

        User.objects.create(
            username=email,
            email=email,
            password=make_password(password),
            first_name=name,
            gender=gender.lower(),
            dob=dob or None,
            rank=rank,           # ✅ assign rank
            role="vvip",
            admin=request.user,
            created_by=request.user,
            category=category_obj,
            phone=phone
        )

        messages.success(request, "VVIP created successfully")
        return redirect("manage_vvip")

    return render(request, "admin_panel/add_vvip.html", context)

@role_required(["admin"])
def edit_vvip(request, vvip_id):
    vvip = get_object_or_404(
        User,
        id=vvip_id,
        role="vvip",
        admin=request.user
    )

    categories = SecurityCategory.objects.filter(admin=request.user)
    ranks = ["PM"] + [c.name for c in categories]  # Or your predefined list of ranks
    is_custom_rank = vvip.rank not in ranks

    context = {
        "vvip": vvip,
        "category": categories,
        "ranks": ranks,
        "is_custom_rank": is_custom_rank
    }

    if request.method == "POST":
        vvip.first_name = request.POST.get("name")
        vvip.email = request.POST.get("email")
        vvip.username = request.POST.get("email")
        vvip.gender = request.POST.get("gender").lower()
        vvip.dob = request.POST.get("dob") or None
        phone = request.POST.get("phone").strip()

        # Rank
        rank = request.POST.get("rank")
        custom_rank = request.POST.get("custom_rank")
        if rank == "other":
            rank = custom_rank
        vvip.rank = rank

        # Category
        category_id = request.POST.get("category")
        vvip.category = get_object_or_404(
            SecurityCategory,
            id=category_id,
            admin=request.user
        )

        # 🔴 Email uniqueness check
        if User.objects.filter(email=request.POST.get("email")).exclude(id=vvip.id).exists():
            messages.error(request, "This email is already registered. Please use a different email.")
            return redirect("edit_vvip", vvip_id=vvip.id)
        
        # 🔴 Phone validation
        if not phone or not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Enter a valid 10-digit phone number.")
            return redirect("edit_vvip", vvip_id=vvip.id)

        # 🔴 Unique phone check
        existing_user = User.objects.filter(phone=phone).exclude(id=vvip.id).first()
        if existing_user:
            messages.error(request, "This phone number is already registered.")
            return render(request, "admin_panel/edit_vvip.html", context)

        vvip.phone = phone
        print("PHONE:", phone)

        vvip.save()
        messages.success(request, "VVIP profile updated successfully")
        return redirect("manage_vvip")

    return render(request, "admin_panel/edit_vvip.html", context)

# @role_required(["admin"])
# def delete_vvip(request, vvip_id):
#     return redirect('manage_vvip')


#----- Custom user Panel Views -----
@role_required(["field_staff"])
def user_assign_duty(request):

    user = request.user

    duties = VVIPDuty.objects.filter(
        field_staff=user,
        is_active=True
    ).select_related("vvip", "category", "assigned_by")

    return render(request, "user_panel/user_assign_duty.html", {
        "duties": duties
    })

from django.contrib import messages

@role_required(["field_staff"])
def request_application_box(request):

    if request.method == "POST":
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        if subject and message:

            # ✅ Save request
            request_obj = FieldStaffRequest.objects.create(
                staff=request.user,
                subject=subject,
                message=message
            )

            # 👮 Get Dedicated Munsi
            munsi_user = request.user.gd_munsi


            # 🔔 Create In-App Notification for Munsi
            notification = Notification.objects.create(
                receiver=munsi_user,
                sender=request.user,
                title="New Staff Request",
                message=f"{request.user.get_full_name() or request.user.username} submitted a new request.",
                notification_type="request",
                priority="high",
                metadata={
                    "staff": request.user.username,
                    "request_id": request_obj.request_number,
                    "subject": request_obj.subject,
                    "note": "Open Staff Requests panel for review"
                }
            )

            # 🔥 WebSocket Real-time Notification
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"user_{munsi_user.id}",
                {
                    "type": "send_status_update",
                    "data": {
                        "title": notification.title,
                        "message": notification.message,
                        "request_id": request_obj.request_number
                    }
                }
            )


            # 🔥 Firebase Push Notification
            send_push_notification(
                id=request_obj.request_number,
                user=munsi_user,
                title="New Request From Staff",
                body=request_obj.subject,
                sender=request.user,
                url=reverse("munsi_field_staff_requests"),
                notification_type="request"
            )

            messages.success(request, "Your request has been submitted successfully.")
            return redirect("request_history")

        else:
            messages.error(request, "Please fill all fields.")

    return render(request, "user_panel/request_application_box.html")


@role_required(["field_staff"])
def request_history(request):

    requests = FieldStaffRequest.objects.filter(
        staff=request.user
    ).order_by("-submitted_at")

    return render(
        request,
        "user_panel/request_history.html",
        {"requests": requests}
    )

@role_required(["field_staff"])
def duty_history(request):
    return render(request, "user_panel/duty_history.html")


@role_required(["field_staff"])
def attendance_panel(request):
    return render(request, "user_panel/attendance_panel.html")

@role_required(["field_staff"])
def user_profile(request):
    return render(request, "user_panel/user_profile.html")

from django.utils import timezone

@role_required(["field_staff"])
def edit_user_profile(request):

    user = request.user

    if request.method == "POST":

        # -------- BASIC INFO --------
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        new_email = request.POST.get("email")

        # 🔴 Email uniqueness check
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                messages.error(request, "Email already in use.")
                return redirect("edit_user_profile")

            # 🔐 Reset verification if email changed
            user.email_verified = False
            user.email_verified_at = None

        user.email = new_email
        user.username = new_email
        user.phone = request.POST.get("phone")

        # -------- PROFILE PHOTO --------
        # REMOVE PHOTO FIRST
        if request.POST.get("remove_photo") == "1":
            if user.profile_photo:
                user.profile_photo.delete(save=False)
            user.profile_photo = None

        # THEN HANDLE NEW UPLOAD
        elif request.FILES.get("profile_photo"):
            user.profile_photo = request.FILES.get("profile_photo")

        # -------- PASSWORD CHANGE --------
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password or confirm_password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("edit_user_profile")

            if len(password) < 6:
                messages.error(request, "Password must be at least 6 characters.")
                return redirect("edit_user_profile")

            user.set_password(password)
            update_session_auth_hash(request, user)

        user.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("user_profile")

    return render(request, "user_panel/edit_user_profile.html")


#-------- CRUD opration by admin to manage user ---------
import openpyxl


@role_required(["developer", "master_admin", "super_admin", "admin", "gd_munsi"])
def add_user(request):
    user = request.user
    context = {
        'police_rank': police_rank,
    }
    action = request.POST.get("action")
    # ==================== YOUR ORIGINAL CODE STARTS HERE (UNCHANGED) ====================
    # 1️⃣ Determine allowed roles...
    if user.role == "developer":
        allowed_roles = ["master_admin"]
    elif user.role == "master_admin":
        allowed_roles = ["super_admin"]
    elif user.role == "super_admin":
        allowed_roles = ["admin"]
    elif user.role == "admin":
        if User.objects.filter(role="gd_munsi", admin=user).exists():
            allowed_roles = ["field_staff"]
        else:
            allowed_roles = ["gd_munsi", "field_staff"]
    elif user.role == "gd_munsi":
        allowed_roles = ["field_staff"]
    else:
        allowed_roles = []

    context["allowed_roles"] = allowed_roles

    # 2️⃣ GD Munsi list...
    if user.role == "admin":
        context["gd_munsi_list"] = User.objects.filter(role="gd_munsi", admin=user)
    elif user.role == "gd_munsi":
        context["gd_munsi_list"] = [user]
    else:
        context["gd_munsi_list"] = []

    # ==================== YOUR ORIGINAL CODE ENDS HERE ====================

    # ====================== NEW: EXCEL BULK UPLOAD LOGIC ======================
        # ====================== EXCEL BULK UPLOAD LOGIC ======================
    if request.method == "POST" and request.FILES.get('excel_file') and action == "preview":
        try:
            excel_file = request.FILES['excel_file']
            file_name = excel_file.name.lower()

            import openpyxl
            import csv
            import io

            rows_data = []

            # ================= CSV SUPPORT =================
            if file_name.endswith('.csv'):
                decoded_file = excel_file.read().decode('utf-8-sig')
                reader = csv.reader(io.StringIO(decoded_file))

                for i, row in enumerate(reader):
                    if i == 0:  # skip header
                        continue
                    rows_data.append(row)

            # ================= EXCEL SUPPORT =================
            elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                wb = openpyxl.load_workbook(excel_file)
                ws = wb.active

                for row in ws.iter_rows(min_row=2, values_only=True):
                    rows_data.append(row)

            # ================= INVALID FILE =================
            else:
                return JsonResponse({
                    "success": False,
                    "error": "Unsupported file format. Upload CSV or Excel."
                }, status=400)

            rank_map = {}

            for r in police_rank:
                full = r["police_rank"]
                short = None

                if "(" in full and ")" in full:
                    short = full.split("(")[-1].replace(")", "").strip()

                rank_map[full.lower()] = full

                if short:
                    rank_map[short.lower()] = full

            preview_data = []

            for row_num, row in enumerate(rows_data, start=2):

                email = str(row[0]).strip() if row[0] else None
                password = str(row[1]).strip() if len(row) > 1 and row[1] else "temp@123"
                rank_name = str(row[2]).strip() if len(row) > 2 and row[2] else None

                row_errors = []

                # ✅ Email validation
                if not email:
                    row_errors.append("Email is required")

                if email and User.objects.filter(email=email).exists():
                    row_errors.append("Email already exists")

                # ✅ Rank mapping
                rank_value = None

                if rank_name:
                    key = rank_name.strip().lower()
                    rank_value = rank_map.get(key)

                    if not rank_value:
                        row_errors.append("Invalid rank")

                # ✅ Append preview
                preview_data.append({
                    "row": row_num,
                    "email": email,
                    "password": password,
                    "rank": rank_value,
                    "errors": row_errors,
                    "is_valid": len(row_errors) == 0
                })

            request.session["bulk_users"] = preview_data
            return JsonResponse({
                "success": True,
                "preview": preview_data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)

    if request.method == "POST" and action == "create_users":
        import json
        from django.db import transaction
        from django.conf import settings

        try:
            all_rows = request.session.get("bulk_users", [])
            selected_indexes = json.loads(request.POST.get("rows", "[]"))
            
            if not selected_indexes:
                return JsonResponse({"success": False, "message": "No rows selected"}, status=400)

            selected_rows = [all_rows[int(i)] for i in selected_indexes if int(i) < len(all_rows)]

            # Pre-fetch existing emails (already good)
            emails = [row.get("email") for row in selected_rows if row.get("email")]
            existing_emails = set(
                User.objects.filter(email__in=emails).values_list("email", flat=True)
            )

            # Hierarchy setup (once, outside loop)
            gd_munsi_obj = None
            admin_obj = request.user

            if request.user.role == "admin":
                gm_id = request.POST.get("gd_munsi_id")
                if gm_id:
                    gd_munsi_obj = User.objects.filter(id=gm_id, role="gd_munsi").first()
            elif request.user.role == "gd_munsi":
                gd_munsi_obj = request.user
                admin_obj = getattr(request.user, 'admin', None)

            users_to_create = []
            errors = []

            default_hash = getattr(settings, 'DEFAULT_BULK_PASSWORD_HASH', None)
            if not default_hash:
                from django.contrib.auth.hashers import make_password
                default_hash = make_password("temp@123")

            for row in selected_rows:
                try:
                    email = row.get("email")
                    if not email or email in existing_emails:
                        continue

                    rank = row.get("rank")

                    # Create model instance
                    new_user = User(
                        username=email,
                        email=email,
                        first_name=email.split('@')[0].title() if email else "",
                        role="field_staff",
                        rank=rank,
                        created_by=request.user,
                        is_active=True,
                        password=default_hash,          # ← Use precomputed hash
                        admin=admin_obj,
                        gd_munsi=gd_munsi_obj,
                    )
                    users_to_create.append(new_user)
                except Exception as e:
                    errors.append(f"{email}: {str(e)}")

            if not users_to_create:
                return JsonResponse({"success": True, "created": 0, "message": "No new users to create"})

            # ================== OPTIMIZED BULK CREATE ==================
            created_count = 0
            batch_size = 400          # ← Much better for Postgres + User model

            # Smaller transactions per batch
            for i in range(0, len(users_to_create), batch_size):
                batch = users_to_create[i:i + batch_size]
                with transaction.atomic():
                    User.objects.bulk_create(
                        batch, 
                        batch_size=batch_size, 
                        ignore_conflicts=True
                    )
                created_count += len(batch)

            # Clean session
            if "bulk_users" in request.session:
                del request.session["bulk_users"]

            return JsonResponse({
                "success": True,
                "created": created_count,
                "errors": len(errors),
                "redirect_url": reverse("manage_users")
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Server error: {str(e)}"
            }, status=500)
    # ====================== ORIGINAL POST HANDLING (UNCHANGED) ======================
    if request.method == "POST" and not request.FILES.get('excel_file'):
        # ... [Your entire original POST logic remains EXACTLY the same] ...
        name = request.POST.get("name")
        email = request.POST.get("email")
        # ... rest of your code unchanged ...
        # (I kept it out for brevity - do NOT modify this block)

    return render(request, "admin_panel/add_user.html", context)

@role_required(["developer", "master_admin", "super_admin", "admin", "gd_munsi"])
def edit_user(request, user_id):

    user = request.user                          # logged in user
    officer = User.objects.get(id=user_id)       # user being edited
    context = {
        'police_rank':police_rank,
    }

    # -----------------------------------------------------
    # Permission Guard (KEEP THIS)
    # -----------------------------------------------------
    if user.role != "developer":

        if user.role == "master_admin" and officer.created_by != user:
            messages.error(request, "Permission denied.")
            return redirect("manage_users")

        if user.role == "super_admin" and officer.created_by != user:
            messages.error(request, "Permission denied.")
            return redirect("manage_users")

        if user.role == "admin" and officer.admin != user:
            messages.error(request, "Permission denied.")
            return redirect("manage_users")

        if user.role == "gd_munsi" and officer.gd_munsi != user:
            messages.error(request, "Permission denied.")
            return redirect("manage_users")


    # -----------------------------------------------------
    # Determine allowed roles based on logged-in user
    # -----------------------------------------------------
    if user.role == "developer":
        allowed_roles = ["master_admin"]

    elif user.role == "master_admin":
        allowed_roles = ["super_admin"]

    elif user.role == "super_admin":
        allowed_roles = ["admin"]

    elif user.role == "admin":
        if officer.role == "gd_munsi":
            allowed_roles = ["gd_munsi"]
        else:
            allowed_roles = ["field_staff"]

    elif user.role == "gd_munsi":
        allowed_roles = ["field_staff"]

    else:
        allowed_roles = []

    context["role"] = allowed_roles
    context["officer"] = officer

    # -----------------------------------------------------
    # Provide GD Munsi dropdown logic
    # -----------------------------------------------------
    if user.role == "admin":
        context["gd_munsi_list"] = User.objects.filter(role="gd_munsi", admin=user)

    elif user.role == "gd_munsi":
        context["gd_munsi_list"] = [user]

    else:
        context["gd_munsi_list"] = []

    # -----------------------------------------------------
    # Handle UPDATE
    # -----------------------------------------------------
    if request.method == "POST":
        officer.first_name = request.POST.get("name")
        officer.email = request.POST.get("email")
        officer.username = request.POST.get("email")
        officer.gender = request.POST.get("gender")
        officer.dob = request.POST.get("dob")
        officer.rank = request.POST.get("rank")
        officer.phone = request.POST.get("phone")

        new_role = request.POST.get("role")

        # -----------------------------------------------------
        # ❌ BLOCK MULTIPLE GD ASSIGNMENT ON EDIT
        # -----------------------------------------------------
        if user.role == "admin" and new_role == "gd_munsi":
            gd_exists = User.objects.filter(
                role="gd_munsi",
                admin=user
            ).exclude(id=officer.id).exists()

            if gd_exists:
                messages.error(
                    request,
                    "You already have a GD Munsi. Cannot assign another."
                )
                return redirect("edit_user", user_id=user_id)

        # 🔴 Email uniqueness check
        if User.objects.filter(email=officer.email).exclude(id=officer.id).exists():
            messages.error(request, "This email is already registered. Please use a different email.")
            return redirect("edit_user", user_id=user_id)

        # ----------------------------
        # Hierarchy Logic
        # ----------------------------
        if user.role == "admin":

            if new_role == "gd_munsi":
                officer.gd_munsi = None
                officer.admin = user

            elif new_role == "field_staff":
                gd_id = request.POST.get("gd_munsi_id")
                if gd_id:
                    gm = User.objects.get(id=gd_id)
                    officer.gd_munsi = gm
                    officer.admin = user

        elif user.role == "gd_munsi":
            if new_role == "field_staff":
                officer.gd_munsi = user
                officer.admin = user.admin

        # Update role last
        officer.role = new_role

        officer.save()

        if officer.role == "field_staff":
            messages.success(request, f"{officer.first_name} as {officer.role} has been updated successfully!")
            return redirect("manage_users")
        elif officer.role == "gd_munsi":
            messages.success(request, f"{officer.first_name} as {officer.role} has been updated successfully!")
            return redirect("manage_users")
        elif user.role == "master_admin":
            messages.success(request, f"{officer.first_name} as {officer.role} has been updated successfully!")
            return redirect("manage_users")
        elif user.role == "super_admin":
            messages.success(request, f"{officer.first_name} as {officer.role} has been updated successfully!")
            return redirect("manage_users")

    return render(request, "admin_panel/edit_user.html", context)


@role_required(["developer", "master_admin", "super_admin", "admin", "gd_munsi"])
def toggle_user_status(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    acting_user = request.user

    # 🔁 Smart redirect (go back to same page)
    redirect_url = request.META.get("HTTP_REFERER", "manage_users")

    # 🚫 Cannot suspend yourself
    if target_user.id == acting_user.id:
        messages.error(request, "You cannot suspend your own account.")
        return redirect(redirect_url)

    # 🚫 Role hierarchy enforcement
    if ROLE_HIERARCHY[acting_user.role] <= ROLE_HIERARCHY[target_user.role]:
        messages.error(request, "You are not allowed to suspend this user.")
        return redirect(redirect_url)

    # 🔐 Scope enforcement
    if acting_user.role == "admin" and target_user.admin != acting_user:
        messages.error(request, "You cannot manage users outside your admin scope.")
        return redirect(redirect_url)

    if acting_user.role == "gd_munsi" and target_user.gd_munsi != acting_user:
        messages.error(request, "You cannot manage users outside your GD scope.")
        return redirect(redirect_url)

    # ✅ Toggle status
    if request.method == "POST":
        target_user.is_active = not target_user.is_active
        target_user.save()

        msg = "activated" if target_user.is_active else "suspended"
        messages.success(request, f"{target_user.username} has been {msg}.")
        return redirect(redirect_url)

    messages.error(request, "Invalid request.")
    return redirect(redirect_url)


#-------- CRUD opration by admin to Manage Police Categories ---------
@role_required(["admin"])
def manage_security_categories(request):
    categories = SecurityCategory.objects.filter(admin_id=request.user.id).order_by("-created_at")

    return render(request,"admin_panel/manage_security_categories.html",{"categories": categories})


@role_required(["admin"])
def add_security_category(request):

    context = {
        'police_rank':police_rank,
        'category' :category,
    }

    # 🔐 Only categories created by THIS admin
    # categories = SecurityCategory.objects.filter(admin=request.user)

    if request.method == "POST":

        category_name = request.POST.get("category_name")
        custom_category = request.POST.get("custom_category", "").strip()

        # Handle custom category
        if category_name == "other":
            category_name = custom_category

        if not category_name:
            messages.error(request, "Category name is required.")
            return redirect(request.path)

        # Prevent duplicate category for same admin
        if SecurityCategory.objects.filter(
            name__iexact=category_name,
            admin_id=request.user.id
        ).exists():
            messages.error(request, "This category already exists.")
            return redirect(request.path)

        personnel_by_rank = {}
        total_personnel = 0

        # Collect rank-wise data
        for key, value in request.POST.items():
            if key.startswith("rank_") and value:
                try:
                    count = int(value)
                    if count > 0:
                        rank_name = key.replace("rank_", "")
                        personnel_by_rank[rank_name] = count
                        total_personnel += count
                except ValueError:
                    continue

        if total_personnel == 0:
            messages.error(
                request,
                "Please enter personnel for at least one rank."
            )
            return redirect(request.path)

        # ✅ Create category (admin-owned)
        SecurityCategory.objects.create(
            name=category_name,
            personnel_by_rank=personnel_by_rank,
            total_personnel=total_personnel,
            admin_id=request.user.id
        )

        messages.success(request,"Security category added successfully.")
        return redirect("manage_security_categories")

    return render(request,"admin_panel/add_security_category.html",context)

@role_required(["admin"])
def edit_security_category(request, category_id):

    category = get_object_or_404(
        SecurityCategory,
        id=category_id,
        admin=request.user   # 🔐 admin scoped
    )

    if request.method == "POST":
        personnel_by_rank = {}
        total_personnel = 0

        for key, value in request.POST.items():
            if key.startswith("rank_") and value:
                try:
                    count = int(value)
                    if count > 0:
                        rank_name = key.replace("rank_", "")
                        personnel_by_rank[rank_name] = count
                        total_personnel += count
                except ValueError:
                    continue

        if total_personnel == 0:
            messages.error(request, "At least one rank is required.")
            return redirect(request.path)

        category.personnel_by_rank = personnel_by_rank
        category.total_personnel = total_personnel
        category.save()

        messages.success(request, "Security category updated successfully.")
        return redirect("manage_security_categories")

    context = {
        "category": category,
        "police_rank": police_rank,  # all available ranks
    }
    return render(request, "admin_panel/edit_security_category.html", context)


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@role_required(["admin"])
def delete_security_category(request, category_id):
    category = get_object_or_404(
        SecurityCategory,
        id=category_id,
        admin=request.user   # 🔐 admin scoped
    )

    if request.method == "POST":
        category.delete()
        messages.success(request, "Security category deleted successfully.")
        return redirect("manage_security_categories")

    # ❌ Do not allow GET delete
    messages.error(request, "Invalid delete request.")
    return redirect("manage_security_categories")


#vvip views
@role_required(["vvip"])
def edit_vvip_profile(request):

    user = request.user

    if request.method == "POST":

        # -------- BASIC INFO --------
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        new_email = request.POST.get("email")

        # 🔴 Email uniqueness check
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                messages.error(request, "Email already in use.")
                return redirect("edit_vvip_profile")

            # 🔐 Reset verification if email changed
            user.email_verified = False
            user.email_verified_at = None

        user.email = new_email
        user.username = new_email  # if using email as username
        user.phone = request.POST.get("phone")

        # -------- PROFILE PHOTO --------
        # REMOVE PHOTO FIRST
        if request.POST.get("remove_photo") == "1":
            if user.profile_photo:
                user.profile_photo.delete(save=False)
            user.profile_photo = None

        # THEN HANDLE NEW UPLOAD
        elif request.FILES.get("profile_photo"):
            user.profile_photo = request.FILES.get("profile_photo")

        # -------- PASSWORD CHANGE --------
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password or confirm_password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("edit_vvip_profile")

            if len(password) < 6:
                messages.error(request, "Password must be at least 6 characters.")
                return redirect("edit_vvip_profile")

            user.set_password(password)
            update_session_auth_hash(request, user)  # 🔥 prevents logout

        user.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("vvip_profile")

    return render(request, "vvip_panel/edit_vvip_profile.html")

@role_required(["vvip"])
def vvip_profile(request):
    return render(request, "vvip_panel/vvip_profile.html")

@role_required(["vvip"])
def vvip_assigned_duty(request):

    user = request.user

    duties = (
        VVIPDuty.objects
        .filter(vvip=user, is_active=True)
        .select_related("vvip", "category", "assigned_by", "field_staff")
        .order_by("field_staff__rank", "-assigned_at")   # 🔥 ADD THIS
    )

    # 🔥 GROUP BY batch_id
    grouped_duties = defaultdict(list)

    for duty in duties:
        grouped_duties[duty.batch_id].append(duty)

    return render(request, "vvip_panel/vvip_assigned_duty.html", {
        "grouped_duties": grouped_duties.values()
    })

@role_required(["vvip"])
def vvip_request_history(request):

    requests = VVIPRequest.objects.filter(
        vvip=request.user
    ).order_by("-submitted_at")

    return render(
        request,
        "vvip_panel/vvip_request_history.html",
        {"requests": requests}
    )

@role_required(["vvip"])
def vvip_request_application_box(request):

    user = request.user
    admin = user.admin

    receivers = User.objects.filter(
        Q(id=admin.id, role="admin") |
        Q(admin=admin, role="gd_munsi")
    )

    if request.method == "POST":
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        receiver_id = request.POST.get("receiver")

        # 🔴 validations
        if not subject or not message or not receiver_id:
            messages.error(request, "All fields are required.")
            return redirect("vvip_request_application_box")

        receiver = User.objects.get(id=receiver_id)

        # 🚫 Safety check
        if receiver not in receivers:
            messages.error(request, "Invalid receiver selected.")
            return redirect("vvip_request_application_box")

        # ✅ Create request
        request_obj = VVIPRequest.objects.create(
            vvip=user,
            receiver=receiver,
            subject=subject,
            message=message
        )

        # =====================================================
        # 🔔 1. IN-APP NOTIFICATION
        # =====================================================
        notification = Notification.objects.create(
            receiver=receiver,
            sender=user,
            title="New VVIP Request",
            message=f"{user.get_full_name() or user.username} sent a new request.",
            notification_type="request",
            priority="high",
            metadata={
                "vvip": user.username,
                "request_id": request_obj.request_number,
                "subject": request_obj.subject,
                "note": "Open VVIP Requests panel"
            }
        )

        # =====================================================
        # 🔥 2. REAL-TIME (WebSocket)
        # =====================================================
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"user_{receiver.id}",
            {
                "type": "send_status_update",
                "data": {
                    "title": notification.title,
                    "message": notification.message,
                    "request_id": request_obj.request_number
                }
            }
        )

        # =====================================================
        # 🔥 3. FIREBASE PUSH
        # =====================================================
        send_push_notification(
            id=request_obj.request_number,
            user=receiver,
            title="New Request From VVIP",
            body=request_obj.subject,
            sender=user,
            url=reverse("centrelize_Notifications"),  # 🔥 create this page
            notification_type="request"
        )

        messages.success(request, "Request sent successfully.")
        return redirect("vvip_request_history")

    return render(request, "vvip_panel/vvip_request_application_box.html", {
        "receivers": receivers
    })






# ------- centralized notification views ------------

@role_required(["field_staff","gd_munsi","admin","super_admin","master_admin","vvip"])
def centrelize_Notifications(request):

    user = request.user

    notifications = (
        Notification.objects
        .filter(
            receiver=user,
            is_deleted=False
        )
        .order_by("-created_at")
    )

    context = {
        "notifications": notifications
    }

    # Select template based on role
    if user.role == "field_staff":
        template = "user_panel/centrelize_Notifications.html"

    elif user.role == "gd_munsi":
        template = "GD_munsi_panel/centrelize_Notifications.html"

    elif user.role == "admin":
        template = "admin_panel/centrelize_Notifications.html"

    elif user.role == "super_admin":
        template = "admin_panel/centrelize_Notifications.html"

    elif user.role == "master_admin":
        template = "admin_panel/centrelize_Notifications.html"

    elif user.role == "vvip":
        template = "vvip_panel/centrelize_Notifications.html"

    else:
        template = "user_panel/centrelize_Notifications.html"

    return render(request, template, context)

@login_required
def mark_notification_read(request, notification_id):

    if request.method == "POST":

        notification = Notification.objects.filter(
            id=notification_id,
            receiver=request.user
        ).first()

        if notification and not notification.is_read:

            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"})

@login_required
def mark_all_notifications_read(request):

    if request.method == "POST":

        Notification.objects.filter(
            receiver=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        return JsonResponse({"status":"success"})

    return JsonResponse({"status":"error"})

@login_required
def archive_notification(request, notification_id):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        receiver=request.user
    )

    notification.is_archived = True
    notification.save(update_fields=["is_archived"])

    return redirect("centrelize_Notifications")


@login_required
def delete_notification(request, notification_id):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        receiver=request.user
    )

    notification.is_deleted = True
    notification.deleted_at = timezone.now()
    notification.save(update_fields=["is_deleted","deleted_at"])

    return JsonResponse({"status":"deleted"})

@login_required
def delete_all_notifications(request):

    if request.method == "POST":

        Notification.objects.filter(
            receiver=request.user,
            is_deleted=False
        ).update(
            is_deleted=True
        )

        return JsonResponse({"status":"success"})

    return JsonResponse({"status":"error"})






#-------------centrelize notify -----------
@role_required(["gd_munsi","admin","super_admin","master_admin"])
def centrelize_notify(request):
    current_user = request.user

    if request.method == "POST":
        title = request.POST.get("title")
        message = request.POST.get("message")
        notify_type = request.POST.get("notify_type")
        scope = request.POST.get("scope")
        target_user_id = request.POST.get("target_user")

        users = User.objects.none()

        # -------- determine receivers --------
        # -------- determine receivers --------
        if current_user.role == "master_admin":

            if scope == "developer":
                users = User.objects.filter(role="developer")

            elif scope == "all_super_admin":
                users = User.objects.filter(role="super_admin")

            elif scope == "specific_super_admin" and target_user_id:
                users = User.objects.filter(
                    id=target_user_id,
                    role="super_admin"
                )


        elif current_user.role == "super_admin":

            if scope == "master_admin":
                users = User.objects.filter(role="master_admin")

            elif scope == "all_admin":
                users = User.objects.filter(
                    role="admin",
                    created_by=current_user
                )

            elif scope == "specific_admin" and target_user_id:
                users = User.objects.filter(
                    id=target_user_id,
                    role="admin",
                    created_by=current_user
                )


        elif current_user.role == "admin":

            if scope == "super_admin":
                users = User.objects.filter(role="super_admin")

            elif scope == "gd_munsi":
                users = User.objects.filter(
                    role="gd_munsi",
                    admin=current_user
                )

            elif scope == "staff":
                users = User.objects.filter(
                    role="field_staff",
                    gd_munsi__admin=current_user
                )
            
            elif scope == "specific_staff" and target_user_id:
                users = User.objects.filter(
                    id=target_user_id,
                    role="field_staff",
                    gd_munsi__admin=current_user
                )

            elif scope == "all_vvip":
                users = User.objects.filter(
                    role="vvip",
                    created_by=current_user
                )

            elif scope == "specific_vvip" and target_user_id:
                users = User.objects.filter(
                    id=target_user_id,
                    role="vvip",
                    created_by=current_user
                )


        elif current_user.role == "gd_munsi":

            if scope == "admin":
                users = User.objects.filter(
                    id=current_user.admin_id
                )

            elif scope == "staff":
                users = User.objects.filter(
                    role="field_staff",
                    gd_munsi=current_user
                )
            
            elif scope == "specific_staff" and target_user_id:
                users = User.objects.filter(
                    id=target_user_id,
                    role="field_staff",
                    gd_munsi=current_user
                )

            elif scope == "all_vvip":
                users = User.objects.filter(
                    role="vvip",
                    created_by=current_user.admin
                )

            elif scope == "specific_vvip" and target_user_id:
                users = User.objects.filter(
                    id=target_user_id,
                    role="vvip",
                    created_by=current_user.admin
                )

        # -------- create notifications --------
        channel_layer = get_channel_layer()

        for user in users:

            notification = Notification.objects.create(
                receiver=user,
                sender=current_user,
                title=title,
                message=message,
                notification_type=notify_type,
                priority="critical" if notify_type == "sos" else "normal",
                metadata={"sent_by": current_user.username}
            )

            # 🔔 Send WebSocket real-time update
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "send_status_update",
                    "data": {
                        "title": notification.title,
                        "message": notification.message,
                        "sender": current_user.username,
                        "type": notify_type
                    }
                }
            )

            # 🔥 Firebase Push Notification
            send_push_notification(
                id=notification.id,
                user=user,
                title=title,
                body=message,
                sender=current_user,
                url=reverse("centrelize_Notifications"),
                notification_type=notify_type
            )

        # -------- log centralized notification --------
        recipient_data = [{"id": u.id, "username": u.username, "role": u.role} for u in users]

        CentralizedNotifyLog.objects.create(
            sender=current_user,
            notify_type=notify_type,
            scope=scope,
            target_user_id=target_user_id if "specific" in scope else None,
            title=title,
            message=message,
            recipients={"count": len(recipient_data), "users": recipient_data}
        )

        messages.success(request, "Notification sent successfully.")
        return redirect("centrelize_notify")

    # -------- prepare users for dropdown --------
    if current_user.role == "master_admin":

        users = User.objects.filter(
            role__in=["developer", "super_admin"]
        )


    elif current_user.role == "super_admin":

        users = User.objects.filter(
            Q(role="master_admin") |
            Q(role="admin", created_by=current_user)
        )


    elif current_user.role == "admin":

        users = User.objects.filter(
            Q(id=current_user.created_by_id) |
            Q(role="gd_munsi", admin=current_user) |
            Q(role="field_staff", gd_munsi__admin=current_user) |
            Q(role="vvip", created_by=current_user)
        )


    elif current_user.role == "gd_munsi":

        users = User.objects.filter(
            Q(id=current_user.admin_id) |
            Q(role="field_staff", gd_munsi=current_user) |
            Q(role="vvip", created_by=current_user.admin)   # ✅ ADD THIS
        )

    # -------- choose template --------
    if current_user.role == "gd_munsi":
        template = "GD_munsi_panel/centrelize_notify.html"
    else:
        template = "admin_panel/centrelize_notify.html"

    return render(request, template, {"users": users})


@role_required(["gd_munsi","admin","super_admin","master_admin"])
def centrelize_notify_history(request):

    current_user = request.user

    # ✅ Everyone sees only their own logs
    logs = CentralizedNotifyLog.objects.filter(
        sender=current_user
    ).order_by("-created_at")

    # -------- choose template --------
    if current_user.role == "gd_munsi":
        template = "GD_munsi_panel/centrelize_notify_history.html"
    else:
        template = "admin_panel/centrelize_notify_history.html"

    return render(request, template, {
        "logs": logs
    })


#---- this section for email verification otp setup -----
from django.conf import settings
@login_required
def send_email_otp(request):

    user = request.user

    # ❌ Prevent spam → check recent OTP
    recent_otp = VerifyEmailOtp.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).first()

    if recent_otp:
        return JsonResponse({
            "status": "error",
            "message": "Please wait before requesting another OTP"
        })

    otp = VerifyEmailOtp.generate_otp()

    VerifyEmailOtp.objects.create(
        user=user,
        otp=otp,
        created_by=user
    )

    send_mail(
        "Email Verification OTP",
        f"Your OTP is {otp}. Valid for 5 minutes.",
        settings.EMAIL_HOST_USER,
        [user.email]
    )

    return JsonResponse({"status": "success"})

@login_required
def verify_email_otp(request):

    data = json.loads(request.body)
    otp_input = data.get("otp")

    user = request.user

    otp_obj = VerifyEmailOtp.objects.filter(
        user=user,
        is_verified=False
    ).order_by("-created_at").first()

    if not otp_obj:
        return JsonResponse({"status": "error", "message": "No OTP found"})

    # 🔓 Unlock if time passed
    otp_obj.unlock_if_time_passed()

    # ❌ If locked
    if otp_obj.is_locked:
        return JsonResponse({
            "status": "error",
            "message": "Too many attempts. Try later."
        })

    # ❌ Expired
    if otp_obj.is_expired():
        return JsonResponse({
            "status": "error",
            "message": "OTP expired"
        })

    # ❌ Wrong OTP
    if otp_obj.otp != str(otp_input):

        otp_obj.attempts += 1

        if otp_obj.attempts >= 5:
            otp_obj.lock()

        otp_obj.save()

        return JsonResponse({
            "status": "error",
            "message": f"Invalid OTP. Attempts left: {otp_obj.remaining_attempts()}"
        })

    # ✅ SUCCESS
    otp_obj.is_verified = True
    otp_obj.save()

    user.email_verified = True
    user.email_verified_at = timezone.now()
    user.save()

    return JsonResponse({
        "status": "success",
        "message": "Email verified successfully"
    })









# #----- firebase push notification -----
# def showFirebaseJS(request):
#     data='importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-app.js");' \
#          'importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-messaging.js"); ' \
#          'var firebaseConfig = {' \
#          '        apiKey: "AIzaSyCEVCeD8QbdOFG1MMk0LKi6FNAoGY3cL9E",' \
#          '        authDomain: "push-notification-cc870.firebaseapp.com",' \
#          '        databaseURL: "",' \
#          '        projectId: "push-notification-cc870",' \
#          '        storageBucket: "push-notification-cc870.firebasestorage.app",' \
#          '        messagingSenderId: "595457578638",' \
#          '        appId: "1:595457578638:web:42a5525e4f017186e4dbdf",' \
#          '        measurementId: "G-E476M6ETBE"' \
#          ' };' \
#          'firebase.initializeApp(firebaseConfig);' \
#          'const messaging=firebase.messaging();' \
#          'messaging.setBackgroundMessageHandler(function (payload) {' \
#          '    console.log(payload);' \
#          '    const notification=JSON.parse(payload);' \
#          '    const notificationOption={' \
#          '        body:notification.body,' \
#          '        icon:notification.icon' \
#          '    };' \
#          '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
#          '});'

#     return HttpResponse(data,content_type="text/javascript")

from user_agents import parse
@csrf_exempt
@login_required
def save_fcm_token(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            token = data.get("token")
            user_agent = data.get("user_agent") or request.META.get("HTTP_USER_AGENT", "")
            device_name = data.get("device_name") or "Unknown Device"

            if not token:
                return JsonResponse({"error": "Token missing"}, status=400)

            ip = request.META.get("REMOTE_ADDR")

            # Safe parsing (even if user_agents not installed)
            browser = "Unknown"
            os = "Unknown"

            try:
                from user_agents import parse
                ua = parse(user_agent)
                browser = ua.browser.family
                os = ua.os.family
            except Exception:
                pass  # Never crash if library missing

            # 1. Deactivate all previous tokens of this user
            FCMToken.objects.filter(user=request.user).update(is_active=False)

            # 2. Create or update current token as active
            FCMToken.objects.update_or_create(
                token=token,
                defaults={
                    "user": request.user,
                    "device_name": device_name,
                    "browser": browser,
                    "os": os,
                    "user_agent": user_agent,
                    "ip_address": ip,
                    "is_active": True  # ✅ mark active
                }
            )

            return JsonResponse({"status": "saved"})

        except Exception as e:
            print("FCM SAVE ERROR:", str(e))
            return JsonResponse({"error": "Server error"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)