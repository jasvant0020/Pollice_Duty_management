from django.urls import re_path
from .consumers import MunsiRequestConsumer

websocket_urlpatterns = [
    re_path(r"ws/munsi-requests/$", MunsiRequestConsumer.as_asgi()),
]