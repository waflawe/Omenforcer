from django.shortcuts import redirect, render, reverse
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import logout
from django.views.generic import View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from services.home_app_utils import *
from home_app.forms import RegisterForm, AuthForm
from services.home_mixins import AddReviewMixin, DropReviewMixin, get_rating_operation_error_message

from typing import Dict, Optional


def home_view(request: HttpRequest) -> HttpResponse:
    return render(request, "home/home.html")


class _ReviewOperationOnErrorMixin(View):
    """ Миксин, содержащий базовый on_erorr метод, который срабатывает при получении ошибки. """

    def on_error(self, user: User, error: Optional[int] = None) -> HttpResponse:
        param = f"show_error={error}" if error else "show_success=True"
        return redirect(f'{reverse("home_app:some_user", kwargs={"username": user.username})}?{param}')


class AddReviewView(_ReviewOperationOnErrorMixin, AddReviewMixin):
    def make_add_review(self, request: HttpRequest, username: str, like: Optional[bool] = True) -> HttpResponse:
        flag, user = self.add_review(request, {"username": username}, like)
        error_redirect = check_flag(self, user, flag)
        return error_redirect if error_redirect else self.on_error(user, None)


class LikeView(AddReviewView):
    def post(self, request: HttpRequest, username: str) -> HttpResponse:
        return self.make_add_review(request, username)


class DislikeView(AddReviewView):
    def post(self, request: HttpRequest, username: str) -> HttpResponse:
        return self.make_add_review(request, username, like=False)


class DropView(_ReviewOperationOnErrorMixin, DropReviewMixin):
    def post(self, request: HttpRequest, username: str) -> HttpResponse:
        flag, user = self.drop_review(request, {"username": username})
        error_redirect = check_flag(self, user, flag)
        return error_redirect if error_redirect else self.on_error(user, None)


class SomeUserView(View):
    def get(self, request: HttpRequest, username: str) -> HttpResponse:
        context = SomeUserViewUtils().some_user_view_utils(request, username)
        error_code = request.GET.get("show_error", False)
        try:
            error = {"error_message": get_rating_operation_error_message(int(error_code)) if error_code else None}
        except ValueError:
            error = {"error_message": None}
        return render(request, "home/some_user.html", context=context | error)


class AuthView(View):
    def get(self, request: HttpRequest, flag_error: Optional[bool] = False,
            form: Optional[Dict] = None) -> HttpResponse:
        if check_is_user_auth(request): return redirect("/")
        context = {
            "form": AuthForm(form),
            "flag_error": flag_error,
            "show_success": request.GET.get("show_success", False)
        }
        return render(request, "home/auth.html", context=context)

    def post(self, request: HttpRequest) -> HttpResponse:
        if check_is_user_auth(request): return redirect("/")
        return AuthViewUtils().auth_view_utils(self, request)


class LogoutView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if check_is_user_auth(request):
            logout(request)
        return redirect(reverse("home_app:home"))


class RegisterView(View):
    def get(self, request: HttpRequest, flag: Optional[bool] = False, form: Optional[Dict] = None) -> HttpResponse:
        if check_is_user_auth(request): return redirect("/")
        context = {"form": RegisterForm(form), "flag": flag}
        return render(request, "home/register.html", context=context)

    def post(self, request: HttpRequest) -> HttpResponse:
        if check_is_user_auth(request): return redirect("/")
        return RegisterViewUtils().register_view_utils(self, request)


class SettingsView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest, flag_success: Optional[bool] = False,
            flag_error: Optional[bool] = False) -> HttpResponse:
        context = SettingsViewUtils().settings_view_get_utils(request, flag_success, flag_error)
        return render(request, "home/settings.html", context=context)

    def post(self, request: HttpRequest) -> HttpResponse:
        return SettingsViewUtils().settings_view_post_utils(self, request)
