"""
ASGI config for trist_draft project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trist_draft.settings')
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import trist_draft.apps.auction_table.routing


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            trist_draft.apps.auction_table.routing.websocket_urlpatterns
        )
    ),
})

# Serve static files in development/testing via Daphne
from channels.staticfiles import StaticFilesWrapper
from django.conf import settings
if settings.DEBUG:
    application = StaticFilesWrapper(application)
