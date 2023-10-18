from django.urls import re_path
from .views import login, launch, get_jwks

urlpatterns = [
    re_path(r'^login/$', login, name='login'),
    re_path(r'^launch/$', launch, name='launch'),
    re_path(r'^jwks/$', get_jwks, name='jwks'),
]
