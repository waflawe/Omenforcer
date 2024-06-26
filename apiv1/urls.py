from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import SimpleRouter

from apiv1.api_views import (
    AddCommentApiView,
    DislikeAPIView,
    DropAPIView,
    GetSectionsAPIView,
    GetSectionTopicsAPIView,
    GetTopicCommentsAPIView,
    GetUserAPIView,
    LikeAPIView,
    TopicViewSet,
    UpdateSettingsApiView,
)

router = SimpleRouter()
router.register(r"topics", TopicViewSet, basename="topics")

# domain.com/api/v1/
urlpatterns = [
    path("", include(router.urls)),
    path("topics/<int:ids>/comments/", GetTopicCommentsAPIView.as_view()),
    path("addcomment/", AddCommentApiView.as_view()),
    #
    path("sections/", GetSectionsAPIView.as_view()),
    path("sections/<str:section>/", GetSectionTopicsAPIView.as_view()),
    #
    path("user/<int:ids>/", GetUserAPIView.as_view()),
    path("reviewuser/like/<int:ids>/", LikeAPIView.as_view()),
    path("reviewuser/dislike/<int:ids>/", DislikeAPIView.as_view()),
    path("reviewuser/drop/<int:ids>/", DropAPIView.as_view()),
    path("updatesettings/", UpdateSettingsApiView.as_view()),
    #
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"))
]
