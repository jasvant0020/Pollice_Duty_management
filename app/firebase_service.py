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

def send_push_notification(user, title, body, url=None, sender=None):
    tokens = list(user.fcm_tokens.values_list("token", flat=True))

    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=f"{body}\nFrom: {sender.get_full_name()}" if sender else body,
        ),
        data={
            "click_url": url or "/",
            "sender_id": str(sender.id) if sender else "",
        },
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)

    for idx, resp in enumerate(response.responses):
        if not resp.success:
            FCMToken.objects.filter(token=tokens[idx]).delete()