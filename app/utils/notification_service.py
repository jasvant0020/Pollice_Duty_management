from app.models import Notification
def send_notification(user, title, message, notification_type, obj=None):

    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_object=obj
    )