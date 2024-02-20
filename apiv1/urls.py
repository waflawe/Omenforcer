from django.urls import path
from . import api_views

# domain.com/api/v1/
urlpatterns = [
    path("sections/", api_views.GetSectionsAPIView.as_view()),
    path("topics/", api_views.GetTopicsAPIView.as_view()),
    path("topics/<str:section>/", api_views.GetTopicsAPIView.as_view()),
    path("topicdetail/<int:ids>/", api_views.GetTopicDetailAPIView.as_view()),
    path("topiccomments/<int:ids>/", api_views.GetTopicCommentsAPIView.as_view()),
    path("user/<int:ids>/", api_views.GetUserAPIView.as_view()),
    path("AddTopic/", api_views.AddTopicApiView.as_view()),
    path("AddComment/", api_views.AddCommentApiView.as_view()),
    path("DeleteTopic/<int:ids>", api_views.DeleteTopicApiView.as_view()),
    path("UpdateSettings/", api_views.UpdateSettingsApiView.as_view()),
]
