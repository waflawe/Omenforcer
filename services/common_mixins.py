from typing import Literal
from django.http import HttpRequest
from home_app.models import UserSettings
from rest_framework.request import Request
from django.contrib.auth.models import User
from forum.settings import MEDIA_ROOT

Context = dict
Error = int


def get_crop_upload_path(path: str) -> str:
    splitted_path = path.split("/")
    filename = splitted_path.pop()
    name, extension = filename.split(".")
    splitted_path.append(f"{name}_crop.{extension}")
    return "/".join(splitted_path)


class UserAvatarMixin(object):
    def get_user_avatar_path(self, user: User) -> str:
        user_avatar_path = UserSettings.objects.get(user=user).avatar.path.split(MEDIA_ROOT)[-1]
        if user_avatar_path.endswith("default-user-icon.jpg"):
            return user_avatar_path
        else:
            t = user_avatar_path.split(".")
            return t[0] + "_crop." + t[1]


class AuthenticationMixin(object):
    def check_is_user_auth(self, request: HttpRequest | Request) -> bool:
        return request.user.is_authenticated


class TimezoneMixin(object):
    def get_timezone(self, request: HttpRequest) -> Literal[False] | str:
        if request.user.is_authenticated:
            return UserSettings.objects.get(user=request.user).timezone
        return False
