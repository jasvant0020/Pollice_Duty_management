import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
import app.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

django_asgi_app = get_asgi_application()

print("🔥 ASGI FILE IS LOADED 🔥")

application = ProtocolTypeRouter({
    "http": ASGIStaticFilesHandler(django_asgi_app),  # 👈 THIS FIXES STATIC
    "websocket": AuthMiddlewareStack(
        URLRouter(
            app.routing.websocket_urlpatterns
        )
    ),
})
