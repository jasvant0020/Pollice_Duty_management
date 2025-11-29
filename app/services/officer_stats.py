# services/officer_stats.py
from django.db.models import Count
from app.models import Officer  # update this import accordingly

def get_rank_status():
    """Rankwise personnel count + status logic (your logic)."""
    
    rank_counts = Officer.objects.values('rank').annotate(personnel_count=Count('id'))

    rank_status = []
    for rc in rank_counts:
        count = rc['personnel_count']
        rank = rc['rank']

        if count >= 10:
            status = "Active"
            badge_color = "green"
        elif 5 <= count < 10:
            status = "Partially Filled"
            badge_color = "yellow"
        else:
            status = "Overloaded"
            badge_color = "red"

        rank_status.append({
            'rank': rank,
            'count': count,
            'status': status,
            'badge_color': badge_color
        })

    return rank_status


def get_role_status():
    role_based_count = Officer.objects.values('role').annotate(personnel_count=Count('id'))

    total_staff_count = 0
    admin_staff_count = 0
    GD_munsi_count = 0
    field_staff_count = 0

    for r in role_based_count:
        count = r['personnel_count']
        role = r['role']

        total_staff_count += count

        if role == "GD Munsi":
            GD_munsi_count += count
        elif role == "Admin":
            admin_staff_count += count
        elif role == "User":
            field_staff_count += count

    return {
        'total_staff_count': total_staff_count,
        'admin_staff_count': admin_staff_count,
        'GD_munsi_count': GD_munsi_count,
        'field_staff_count': field_staff_count
    }


def get_global_officer_stats():
    """Expandable global statistics (dashboard, overview, etc.)."""

    return {
        "rank_status": get_rank_status(),
        "total_personnel": Officer.objects.count(),
        "vvip_count": Officer.objects.filter(role="Admin").count(),
        # Add more computed stats as required...
    }
