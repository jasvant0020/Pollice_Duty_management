import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError
from .models import FCMToken

cred = credentials.Certificate("firebase-admin.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)


def send_push_notification(user, title, body):
    tokens = list(user.fcm_tokens.values_list("token", flat=True))

    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)

    # Auto remove invalid tokens
    for idx, resp in enumerate(response.responses):
        if not resp.success:
            FCMToken.objects.filter(token=tokens[idx]).delete()
