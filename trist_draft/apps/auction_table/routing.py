from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from . import consumers
from django.conf.urls import url

websocket_urlpatterns = [
    url(r'^ws/auction_table/', consumers.AuctionConsumer.as_asgi()),
]