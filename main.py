import os
import firebase_admin
from firebase_admin import credentials, messaging


def notify():
    print("sending notification")
    cred_path = os.environ.get("FIREBASE_CREDENTIALS_FILE", "fb_notify.json")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

    message = messaging.Message(
        notification=messaging.Notification(
            title='new message',
            body='hellow world'
        ),
        token=os.environ.get("FCM_TOKEN", "")
    )
    messaging.send(message)


if __name__ == "__main__":
    notify()
