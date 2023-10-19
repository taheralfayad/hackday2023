from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from chatbot import consumers

websocket_urlpatterns = [
    path('ws/messaging/', consumers.YourConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': URLRouter(websocket_urlpatterns),
})
