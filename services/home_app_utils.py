from __future__ import annotations

from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import redirect, reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User

from services.common_utils import get_user_avatar_path, Context, RequestHost
from services.home_mixins import UpdateSettingsMixin, AddReviewMixin
from home_app.forms import UploadAvatarForm, AuthForm, RegisterForm
from home_app.models import UserReviews, UserSettings, Review
from services.user_settings_core import E
from services.forum_mixins import BaseContextMixin

from random import randrange
from typing import Literal, NoReturn
import pytz


def check_flag(view_self, user: User, flag: Literal[False] | E) \
        -> NoReturn | HttpResponse | Literal[None]:
    if flag:
        if flag == 1: raise PermissionDenied
        if flag == 2: raise Http404
        if flag in (3, 4): return view_self.on_error(user, flag)


class SomeUserViewUtils(AddReviewMixin, BaseContextMixin):
    def some_user_view_utils(self, request: HttpRequest, username: str) -> Context | E:
        context = self.get_base_context(request, get_tzone=True)
        flag, user = self.check_perms(request, {"username": username})
        like = Review.objects.filter(reviewer=request.user, user=user).first() if request.user.is_authenticated else None
        return context | {
            "user": user,
            "image": get_user_avatar_path(user)[0],
            "any_random_integer": randrange(100000),
            "show_active": "active" if request.user == user else "",
            "user_rating": UserReviews.objects.get(user=user).rating,
            "reviews_count": Review.objects.filter(user=user).count(),
            "like": ("Лайк" if like.feedback else "Дизлайк") if like else None,
            "form": not isinstance(flag, E),
            "flag": request.GET.get("show_success", False),
            "error": request.GET.get("show_error_3", False),
            "error4": request.GET.get("show_error_4", False),
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
            UserReviews.objects.create(user=user)
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
