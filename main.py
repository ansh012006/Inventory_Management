import firebase_admin
from firebase_admin import credentials, messaging

def notify():
    print("sending notification")
    cred = credentials.Certificate('C:\\Users\\asus\\PycharmProjects\\inventory\\fb_notify.json')
    firebase_admin.initialize_app(cred)

    message = messaging.Message(
        notification=messaging.Notification(
            title='new message',
            body='hellow world'
        ),
        token='cjueTYrUs6cl8tlC-Np5P5:APA91bEt1rvCe9CA0dVPSRbAqQE1EQ3YTyCfih4dw5fB6r7iKnJiuAEz_PKJgzchyF7YGW4dd37uhLvCGldXJyRH8cu9l0oGLZhCCku-i8Slg2i6OUevFtc'
    )
    messaging.send(message)

notify()