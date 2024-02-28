from django.urls import path, include
from apiv1.api_views import (TopicViewSet, UpdateSettingsApiView, GetSectionsAPIView, GetTopicCommentsAPIView,
                             GetUserAPIView, AddCommentApiView, GetSectionTopicsAPIView, DislikeAPIView, LikeAPIView,
                             DropAPIView)
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(r"topics", TopicViewSet, basename="topics")

# domain.com/api/v1/
urlpatterns = [
    path("", include(router.urls)),
    path("sections/", GetSectionsAPIView.as_view()),
    path("sections/<str:section>/", GetSectionTopicsAPIView.as_view()),
    path("topics/<int:ids>/comments/", GetTopicCommentsAPIView.as_view()),
    path("user/<int:ids>/", GetUserAPIView.as_view()),
    path("dislike_user/<int:ids>/", DislikeAPIView.as_view()),
    path("like_user/<int:ids>/", LikeAPIView.as_view()),
    path("drop_review/<int:ids>/", DropAPIView.as_view()),
    path("AddComment/", AddCommentApiView.as_view()),
    path("UpdateSettings/", UpdateSettingsApiView.as_view()),
]
