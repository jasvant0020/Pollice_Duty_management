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

        # Your status logic (can be edited anytime)
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


def get_global_officer_stats():
    """Expandable global statistics (dashboard, overview, etc.)."""

    return {
        "rank_status": get_rank_status(),
        "total_personnel": Officer.objects.count(),
        "vvip_count": Officer.objects.filter(role="Admin").count(),
        # Add more computed stats as required...
    }
