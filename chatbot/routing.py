from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/messaging/$', consumers.Consumer.as_asgi()),
]
