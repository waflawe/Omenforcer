from django.urls import path
from . import views

app_name = "home_app"

# domain.com/
urlpatterns = [
    path("", views.home_view, name="home"),
    path("auth/", views.AuthView.as_view(), name="auth"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("<str:username>/", views.some_user_view, name="some_user"),
]
