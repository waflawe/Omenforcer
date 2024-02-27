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
    path("account/<str:username>/", views.SomeUserView.as_view(), name="some_user"),
    path("account/like/<int:ids>/", views.LikeView.as_view(), name="like"),
    path("account/dislike/<int:ids>/", views.DislikeView.as_view(), name="dislike"),
    path("account/drop/<int:ids>/", views.DropView.as_view(), name="drop")
]
