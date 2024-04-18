from __future__ import annotations

from random import randrange
from typing import Dict, Literal, NoReturn, Optional, Type

import pytz
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, reverse
from rest_framework.request import Request

from home_app.forms import AuthForm, ChangeSignatureForm, RegisterForm, UploadAvatarForm
from home_app.models import UserRating
from schemora.core.enums import RequestHost
from schemora.core.types import E
from schemora.settings.helpers import get_user_avatar_path, get_user_settings, get_user_settings_model
from services.common_utils import Context
from services.forum_mixins import BaseContextMixin
from services.home_mixins import AddReviewMixin, GetUserReviewsInformationMixin, UpdateSettingsMixin

UserSettings = get_user_settings_model()


def check_is_user_auth(request: HttpRequest | Request) -> bool:
    return request.user.is_authenticated


def check_flag(view_self, user: User | Literal[False], flag: Literal[None] | E) \
        -> NoReturn | Literal[None]:
    """
    Функция для анализа полученного при проверке прав на операции с рейтингом флага
    и возвращения соответствующей ему ошибки.
    """

    if flag:
        assert not flag == 1, PermissionDenied
        assert not flag == 2, Http404
        if flag in (3, 4):
            return view_self.on_error(user, flag)
    return None


class SomeUserViewUtils(AddReviewMixin, BaseContextMixin, GetUserReviewsInformationMixin):
    def some_user_view_utils(self, request: HttpRequest, username: str) -> Context | NoReturn:
        context = self.get_base_context(request, get_tzone=True)
        flag, user = self.check_perms(request, {"username": username})
        if not user:
            raise Http404
        image, user_settings = get_user_avatar_path(user)
        return context | self.get_user_reviews_info(request.user, user) | {
            "user": user,
            "image": image,
            "user_signature": user_settings.signature,
            "any_random_integer": randrange(100000),
            "show_active": "active" if request.user == user else "",
            "form": not isinstance(flag, E),
            "show_success": request.GET.get("show_success", False),
        }


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
            UserRating.objects.create(user=user)
            cache.delete(settings.LAST_JOINED_CACHE_NAME)
            return redirect(f"{reverse('home_app:auth')}?show_success=True")

        return view_self.get(request, True, request.POST)


class SettingsViewUtils(UpdateSettingsMixin):
    forms: Dict[str, Type[forms.ModelForm] | forms.ModelForm] = {
        "avatar_form": UploadAvatarForm,
        "signature_form": ChangeSignatureForm
    }
    request_host = RequestHost.VIEW

    def settings_view_get_utils(self, request: HttpRequest, flag_success: Optional[bool] = None,
                                flag_error: Optional[bool] = None) -> Context:
        data = {"signature": get_user_settings(request.user).signature}
        self.forms["signature_form"] = self.forms["signature_form"](data)
        return Context({
            "tzs": pytz.common_timezones,
            "flag_error": flag_error,
            "flag_success": flag_success,
            "forms": self.forms
        })

    def settings_view_post_utils(self, view_self, request: HttpRequest) -> HttpResponse:
        flag_error, flag_success = self.update_settings(request.user, request.POST, request.FILES)
        if flag_error:
            return view_self.get(request, flag_error=flag_error, flag_success=False)
        return redirect(f'{reverse("home_app:some_user", kwargs={"username": request.user.username})}'
                        f'?show_success=True')
