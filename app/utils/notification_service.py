from app.models import Notification
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings



class NotificationService:

    @staticmethod
    def send_notification(
        user,
        title,
        message,
        notification_type,
        obj=None,
        priority="normal"
    ):
        """
        Send notification to a single user
        """

        content_type = None
        object_id = None

        if obj:
            content_type = ContentType.objects.get_for_model(obj)
            object_id = obj.id

        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            content_type=content_type,
            object_id=object_id,
        )

    @staticmethod
    def send_bulk_notification(
        users,
        title,
        message,
        notification_type,
        obj=None,
        priority="normal"
    ):
        """
        Send notification to multiple users
        """

        content_type = None
        object_id = None

        if obj:
            content_type = ContentType.objects.get_for_model(obj)
            object_id = obj.id

        notifications = []

        for user in users:
            notifications.append(
                Notification(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    content_type=content_type,
                    object_id=object_id,
                )
            )

        Notification.objects.bulk_create(notifications)

        return notifications

    @staticmethod
    def mark_as_read(notification):
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])

    @staticmethod
    def mark_all_as_read(user):
        Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    @staticmethod
    def unread_count(user):
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).count()