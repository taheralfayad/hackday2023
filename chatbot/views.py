import datetime
import os

from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.urls import reverse
from pylti1p3.contrib.django import DjangoOIDCLogin, DjangoMessageLaunch, DjangoCacheDataStorage
from pylti1p3.deep_link_resource import DeepLinkResource
from pylti1p3.grade import Grade
from pylti1p3.lineitem import LineItem
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration
from django.views.decorators.csrf import csrf_exempt

from .tasks import send_message_back


PAGE_TITLE = 'Chat'

class ExtendedDjangoMessageLaunch(DjangoMessageLaunch):

    def validate_nonce(self):
        """
        Used to bypass nonce validation for canvas.

        """
        iss = self.get_iss()
        deep_link_launch = self.is_deep_link_launch()
        if iss == "https://canvas.instructure.com" and deep_link_launch:
            return self
        return super().validate_nonce()


def get_lti_config_path():
    return os.path.join(settings.BASE_DIR, 'configs', 'chatbot.json')


def get_tool_conf():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    return tool_conf


def get_launch_data_storage():
    return DjangoCacheDataStorage()


def get_launch_url(request):
    target_link_uri = request.POST.get('target_link_uri', request.GET.get('target_link_uri'))
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')
    return target_link_uri

@csrf_exempt
def login(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()

    oidc_login = DjangoOIDCLogin(request, tool_conf, launch_data_storage=launch_data_storage)
    target_link_uri = get_launch_url(request)

    return oidc_login.enable_check_cookies().redirect(target_link_uri)

@csrf_exempt
def launch(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedDjangoMessageLaunch(request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    course_id = message_launch_data["https://purl.imsglobal.org/spec/lti/claim/custom"]["canvas_course_id"]

    cache.set("course_id", course_id, 3600)

    return render(request, 'chatbot.html', {
        'page_title': PAGE_TITLE,
        'is_deep_link_launch': message_launch.is_deep_link_launch(),
        'launch_data': message_launch.get_launch_data(),
        'launch_id': message_launch.get_launch_id(),
    })


def get_jwks(request):
    tool_conf = get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)

@csrf_exempt
def handle_message(request):
    print(request.session.keys())
    course_id = cache.get("course_id")
    if request.method == "POST":
        user_message = request.POST.get('message')
        send_message_back.delay(user_message, course_id)
        return JsonResponse({'status': 'success', 'message': 'Message received'})
