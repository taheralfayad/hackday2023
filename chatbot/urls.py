from django.urls import re_path
from .views import login, launch, get_jwks, handle_message

urlpatterns = [
    re_path(r'^login/$', login, name='login'),
    re_path(r'^launch/$', launch, name='launch'),
    re_path(r'^jwks/$', get_jwks, name='jwks'),
    re_path(r'^message/$', handle_message, name='handle_message'),
]
