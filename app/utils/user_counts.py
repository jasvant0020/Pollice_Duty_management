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
