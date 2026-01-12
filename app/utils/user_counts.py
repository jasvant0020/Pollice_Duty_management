from django.db.models import Count, Q
from app.models import User,SecurityCategory


def get_admin_staff_counts(admin_user):
    counts = User.objects.filter(admin=admin_user).aggregate(
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
    super_admins = User.objects.filter(
        role="super_admin",
        created_by=master_admin
    )

    data = []

    for sa in super_admins:
        # Admins created by this Super Admin
        admins = User.objects.filter(
            role="admin",
            created_by=sa
        )

        admin_ids = admins.values_list("id", flat=True)

        # Staff under those admins
        staff_counts = User.objects.filter(
            admin_id__in=admin_ids
        ).aggregate(
            gd_munsi=Count("id", filter=Q(role="gd_munsi")),
            field_staff=Count("id", filter=Q(role="field_staff")),
        )

        data.append({
            "id": sa.id,
            "name": sa.get_full_name() or sa.username,
            "admin_count": admins.count(),
            "gd_munsi_count": staff_counts["gd_munsi"] or 0,
            "field_staff_count": staff_counts["field_staff"] or 0,
        })

    return data

def get_admin_dashboard_data(super_admin):
    """
    For Super Admin:
    returns admin-wise cards with staff counts
    """
    admins = User.objects.filter(
        role="admin",
        created_by=super_admin
    )

    data = []

    for admin in admins:
        staff_counts = User.objects.filter(
            admin=admin
        ).aggregate(
            gd_munsi=Count("id", filter=Q(role="gd_munsi")),
            field_staff=Count("id", filter=Q(role="field_staff")),
        )

        data.append({
            "id": admin.id,
            "name": admin.get_full_name() or admin.username,
            "gd_munsi_count": staff_counts["gd_munsi"] or 0,
            "field_staff_count": staff_counts["field_staff"] or 0,
        })

    return data
