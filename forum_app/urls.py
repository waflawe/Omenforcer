from django.urls import path
from forum_app import views

app_name = "forum_app"

# domain.com/forum/
urlpatterns = [
    path("", views.forum_home_view, name="home"),
    path("add_topic/", views.AddTopicView.as_view(), name="add_topic"),
    path("my_topics/", views.SomeUserTopicsView.as_view(), name="my_topics"),
    path("search/", views.search_view, name="search"),
    path("<str:section>/", views.some_section_view, name="some_section"),
    path("<str:section>/<int:ids>/", views.some_id_view, name="some_id"),
    path("<str:section>/<int:ids>/add_comment/", views.AddCommentView.as_view(), name="add_comment"),
    path("<str:section>/<int:ids>/delete/", views.DeleteTopicView.as_view(), name="delete_topic"),
]
