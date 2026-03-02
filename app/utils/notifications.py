# utils/notifications.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from app.models import Notification


def create_notification(user, title, message, notification_type, related_obj=None):

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_object_id=related_obj.id if related_obj else None,
        related_model=related_obj.__class__.__name__ if related_obj else None
    )

    # 🔥 Send WebSocket
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_status_update",
            "data": {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "type": notification.notification_type,
                "created_at": notification.created_at.isoformat(),
            }
        }
    )

    return notification