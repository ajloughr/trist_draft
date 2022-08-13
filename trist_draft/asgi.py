"""
ASGI config for trist_draft project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import trist_draft.apps.auction_table.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trist_draft.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            trist_draft.apps.auction_table.routing.websocket_urlpatterns
        ) 
    ),
    # Just HTTP for now. (We can add other protocols later.)
})
