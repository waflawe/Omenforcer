from __future__ import annotations

from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, reverse, get_object_or_404
from django.contrib.auth.models import User

from services.common_utils import get_timezone, get_user_avatar_path, Context, RequestHost
from services.home_mixins import UpdateSettingsMixin
from home_app.forms import UploadAvatarForm, AuthForm, RegisterForm, UserSettings

from random import randrange
import pytz


class SomeUserViewUtils(object):
    def some_user_view_utils(self, request: HttpRequest, username: str) -> Context:
        user = get_object_or_404(User, username=username)
        return Context({
            "user": user,
            "tzone": get_timezone(request),
            "image": get_user_avatar_path(user)[0],
            "any_random_integer": randrange(100000),
            "flag": request.GET.get("show_success", False)
        })


class AuthViewUtils(object):
    def auth_view_utils(self, view_self, request: HttpRequest) -> HttpResponse:
        form = AuthForm(request.POST)

        if form.is_valid():
            user = authenticate(username=request.POST["username"], password=request.POST["password"])

            if user is not None:
                login(request, user)
                return redirect("/")

        return view_self.get(request, True, request.POST)


class RegisterViewUtils(object):
    def register_view_utils(self, view_self, request: HttpRequest) -> HttpResponse:
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            UserSettings.objects.create(user=user)
            return redirect(f"{reverse('home_app:auth')}?show_success=True")

        return view_self.get(request, True, request.POST)


class SettingsViewUtils(UpdateSettingsMixin):
    validation_class = UploadAvatarForm
    request_host = RequestHost.VIEW

    def settings_view_get_utils(self, request: HttpRequest, flag_success: bool, flag_error: bool) -> Context:
        return Context({
            "tzs": pytz.common_timezones,
            "flag_error": flag_error,
            "flag_success": flag_success,
            "form": self.validation_class()
        })

    def settings_view_post_utils(self, view_self, request: HttpRequest) -> HttpResponse:
        flag_error, flag_success = self.update_settings(request.user, request.POST, request.FILES)
        if flag_error:
            return view_self.get(request, flag_error=flag_error, flag_success=False)
        return redirect(f'{reverse("home_app:some_user", kwargs={"username": request.user.username})}'
                        f'?show_success=True')
