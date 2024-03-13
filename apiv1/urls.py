from django.urls import path, include
from apiv1.api_views import (
    TopicViewSet, UpdateSettingsApiView, GetSectionsAPIView, GetTopicCommentsAPIView, GetUserAPIView, AddCommentApiView,
    GetSectionTopicsAPIView, DislikeAPIView, LikeAPIView, DropAPIView
)
from rest_framework.routers import SimpleRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = SimpleRouter()
router.register(r"topics", TopicViewSet, basename="topics")

# domain.com/api/v1/
urlpatterns = [
    path("", include(router.urls)),
    path("topics/<int:ids>/comments/", GetTopicCommentsAPIView.as_view()),
    path("add_comment/", AddCommentApiView.as_view()),
    #
    path("sections/", GetSectionsAPIView.as_view()),
    path("sections/<str:section>/", GetSectionTopicsAPIView.as_view()),
    #
    path("user/<int:ids>/", GetUserAPIView.as_view()),
    path("like_user/<int:ids>/", LikeAPIView.as_view()),
    path("dislike_user/<int:ids>/", DislikeAPIView.as_view()),
    path("drop_review/<int:ids>/", DropAPIView.as_view()),
    path("update_settings/", UpdateSettingsApiView.as_view()),
    #
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"))
]
