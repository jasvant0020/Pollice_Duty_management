from firebase_admin import messaging
from .models import FCMToken
import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError
from .models import FCMToken

def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase-admin.json")
        firebase_admin.initialize_app(cred)

# Call initialize immediately
initialize_firebase()

def send_push_notification(user, title, body, url=None, sender=None, notification_type="request"):
    tokens = list(user.fcm_tokens.values_list("token", flat=True))

    if not tokens:
        return

    # ✅ Decide notification body based on type
    if notification_type == "request":
        # Staff → Munsi (show full details)
        notification_body = (
            f"\nName: {sender.get_full_name()}\n"
            f"Email: {sender.email}\n"
            f"Rank: {sender.rank}"
        )

    elif notification_type == "status":
        # Munsi → Staff (only show status)
        notification_body = (
            # f"📌 {title}\n\n"
            f"Subject: {body}"
        )

    else:
        # Default fallback
        notification_body = body

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=notification_body,
        ),
        data={
            "click_url": url or "/",
            "sender_id": str(sender.id) if sender else "",
            "type": notification_type,
        },
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)

    # ✅ Remove invalid tokens (your original logic preserved)
    for idx, resp in enumerate(response.responses):
        if not resp.success:
            FCMToken.objects.filter(token=tokens[idx]).delete()