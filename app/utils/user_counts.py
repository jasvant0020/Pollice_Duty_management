from django.db.models import Count, Q
from app.models import User,SecurityCategory, VVIPDuty


def get_admin_staff_counts(admin_user):
    counts = User.objects.filter(admin=admin_user,is_active=True).aggregate(
        total_staff=Count("id", filter=Q(role__in=["field_staff", "gd_munsi"])),
        field_staff=Count("id", filter=Q(role="field_staff")),
        gd_munsi=Count("id", filter=Q(role="gd_munsi")),
    )

    category_count = SecurityCategory.objects.filter(admin_id=admin_user.id).count()

    return {
        "total_staff_count": counts["total_staff"],
        "field_staff_count_admin_id": counts["field_staff"],
        "gd_munsi_count_admin_id": counts["gd_munsi"],
        "security_category_count": category_count,
    }


def get_super_admin_dashboard_data(master_admin):
    """
    Returns data for master admin dashboard:
    - Each super admin
    - Total admins under them
    - GD Munsi & Field Staff counts
    - Admins details for overlay
    """
    super_admins = User.objects.filter(
        role="super_admin",
        created_by=master_admin,
        is_active=True
    )

    data = []

    for sa in super_admins:
        # Admins created by this Super Admin
        admins = User.objects.filter(
            role="admin",
            created_by=sa,
            is_active=True
        )

        admin_ids = admins.values_list("id", flat=True)

        # Staff under those admins
        staff_counts = User.objects.filter(
            admin_id__in=admin_ids,
            is_active=True
        ).aggregate(
            gd_munsi=Count("id", filter=Q(role="gd_munsi")),
            field_staff=Count("id", filter=Q(role="field_staff")),
            vvip=Count("id", filter=Q(role="vvip")),
        )

        # ✅ Individual admin details for overlay
        admins_data = []
        for admin in admins:
            sub_staff_counts = User.objects.filter(admin=admin,is_active=True).aggregate(
                gd_munsi=Count("id", filter=Q(role="gd_munsi")),
                field_staff=Count("id", filter=Q(role="field_staff")),
                vvip=Count("id", filter=Q(role="vvip")),
            )
            admins_data.append({
                "id": admin.id,
                "name": admin.get_full_name() or admin.username,
                "email": admin.email,
                "gd_munsi_count": sub_staff_counts["gd_munsi"] or 0,
                "field_staff_count": sub_staff_counts["field_staff"] or 0,
                "vvip_count": sub_staff_counts["vvip"] or 0,
            })

        data.append({
            "id": sa.id,
            "name": sa.get_full_name() or sa.username,
            "admin_count": admins.count(),
            "gd_munsi_count": staff_counts["gd_munsi"] or 0,
            "field_staff_count": staff_counts["field_staff"] or 0,
            "vvip_count": staff_counts["vvip"] or 0,
            "admins": admins_data,  # ✅ Added this for overlay
        })

    return data



def get_admin_dashboard_data(super_admin):
    admins = User.objects.filter(
        role="admin",
        created_by=super_admin,
        is_active=True
    )

    data = []

    for admin in admins:
        staff = User.objects.filter(admin=admin, is_active=True)

        staff_counts = staff.aggregate(
            gd_munsi=Count("id", filter=Q(role="gd_munsi")),
            field_staff=Count("id", filter=Q(role="field_staff")),
            vvip=Count("id", filter=Q(role="vvip")),
        )

        # ✅ ACTIVE DUTIES UNDER THIS ADMIN
        active_duty_count = VVIPDuty.objects.filter(
            field_staff__admin=admin,
            is_active=True
        ).count()

        # ✅ GD MUNSI DUTY COUNTS
        gd_users = staff.filter(role="gd_munsi")

        gd_data = []
        for gd in gd_users:
            gd_active_duty = gd.gd_assigned_duties.filter(
                is_active=True
            ).count()

            gd_data.append({
                "id": gd.id,
                "name": gd.get_full_name() or gd.username,
                "email": gd.email,
                "active_duty_count": gd_active_duty,
            })

        data.append({
            "id": admin.id,
            "name": admin.get_full_name() or admin.username,
            "gd_munsi_count": staff_counts["gd_munsi"] or 0,
            "field_staff_count": staff_counts["field_staff"] or 0,
            "vvip_count": staff_counts["vvip"] or 0,
            "active_duty_count": active_duty_count,  # admin total duty
            "gd_users": gd_data,  # 🔥 NEW
            "staff": list(
                staff.values("id", "username", "email", "role")
            )
        })

    return data
