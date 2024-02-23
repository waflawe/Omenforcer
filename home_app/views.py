from django.shortcuts import redirect, render, reverse
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import logout
from django.views.generic import View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from services.home_app_utils import *
from services.common_utils import check_is_user_auth
from home_app.forms import RegisterForm, AuthForm

from typing import Dict, Optional


def home_view(request: HttpRequest) -> HttpResponse:
    return render(request, "home/home.html")


class AuthView(View):
    def get(self, request: HttpRequest, flag_error: Optional[bool] = False,
            form: Optional[Dict] = None) -> HttpResponse:
        if check_is_user_auth(request): return redirect("/")
        return render(request, "home/auth.html", context={"form": AuthForm(form), "flag_error": flag_error,
                                                          "show_success": request.GET.get("show_success", False)})

    def post(self, request: HttpRequest) -> HttpResponse:
        if check_is_user_auth(request): return redirect("/")
        return AuthViewUtils().auth_view_utils(self, request)


class LogoutView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        return redirect(reverse("home_app:home"))


class RegisterView(View):
    def get(self, request: HttpRequest, flag: Optional[bool] = False, form: Optional[Dict] = None) -> HttpResponse:
        if check_is_user_auth(request): return redirect("/")
        return render(request, "home/register.html", context={"form": RegisterForm(form), "flag": flag})

    def post(self, request: HttpRequest) -> HttpResponse:
        if check_is_user_auth(request): return redirect("/")
        return RegisterViewUtils().register_view_utils(self, request)


def some_user_view(request: HttpRequest, username: str) -> HttpResponse:
    return render(request, "home/some_user.html", context=SomeUserViewUtils().some_user_view_utils(request, username))


class SettingsView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest, flag_success: Optional[bool] = False,
            flag_error: Optional[bool] = False) -> HttpResponse:
        context = SettingsViewUtils().settings_view_get_utils(request, flag_success, flag_error)
        return render(request, "home/settings.html", context=context)

    def post(self, request: HttpRequest) -> HttpResponse:
        return SettingsViewUtils().settings_view_post_utils(self, request)
