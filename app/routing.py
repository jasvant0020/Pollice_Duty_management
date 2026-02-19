from django.urls import re_path
from . import consumers
from .consumers import MunsiRequestConsumer

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/munsi-requests/$', MunsiRequestConsumer.as_asgi()),
]
