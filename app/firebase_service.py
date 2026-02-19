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

def send_push_notification(user, title, body, url=None):
    tokens = list(user.fcm_tokens.values_list("token", flat=True))

    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data={
            "click_url": url or "/",
            "custom_message": body,
        },
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)

    # Remove invalid tokens
    for idx, resp in enumerate(response.responses):
        if not resp.success:
            FCMToken.objects.filter(token=tokens[idx]).delete()
