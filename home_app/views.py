from django.shortcuts import redirect, render, reverse
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import logout
from django.views.generic import View

from services.home_app_utils import *
from services.common_mixins import AuthenticationMixin
from .forms import *

from typing import Dict, Optional


def home_view(request: HttpRequest) -> HttpResponse:
    return render(request, "home/home.html")


class AuthView(View):
    def get(self, request: HttpRequest, flag_error: Optional[bool] = False,
            form: Optional[Dict] = None) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request): return redirect("/")
        return render(request, "home/auth.html", context={"form": AuthForm(form), "flag_error": flag_error,
                                                          "show_success": request.GET.get("show_success", False)})

    def post(self, request: HttpRequest) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request): return redirect("/")
        return AuthViewUtils().auth_view_utils(self, request)


class LogoutView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request):
            logout(request)
        return redirect(reverse("home_app:auth"))


class RegisterView(View):
    def get(self, request: HttpRequest, flag: Optional[bool] = False, form: Optional[Dict] = None) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request): return redirect("/")
        return render(request, "home/register.html", context={"form": RegisterForm(form), "flag": flag})

    def post(self, request: HttpRequest) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request): return redirect("/")
        return RegisterViewUtils().register_view_utils(self, request)


def some_user_view(request: HttpRequest, username: str) -> HttpResponse:
    return render(request, "home/some_user.html", context=SomeUserViewUtils().some_user_view_utils(request, username))


class SettingsView(View):
    def get(self, request: HttpRequest, flag_success: Optional[bool] = False,
            flag_error: Optional[bool] = False) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request):
            context = SettingsViewUtils().settings_view_get_utils(request, flag_success, flag_error)
            return render(request, "home/settings.html", context=context)

        return redirect(reverse("home_app:auth"))

    def post(self, request: HttpRequest) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request):
            return SettingsViewUtils().settings_view_post_utils(self, request)

        return redirect(reverse("home_app:auth"))
