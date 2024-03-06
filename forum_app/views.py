from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.urls import reverse_lazy

from services.forum_app_utils import *
from forum_app.forms import AddTopicForm

from typing import Optional


def forum_home_view(request: HttpRequest) -> HttpResponse:
    return render(request, "forum/home.html", context=ForumHomeViewUtils().forum_home_view_utils(request))


def search_view(request: HttpRequest) -> HttpResponse:
    return render(request, "forum/search.html", context=SearchViewUtils().search_view_utils(request))


class AddTopicView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest, flag_error: Optional[bool] = False) -> HttpResponse:
        return render(request, "forum/add_topic.html", context={
            "form": AddTopicForm(),
            "flag_error": flag_error,
            "forum": True
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        return AddTopicViewUtils().add_topic_view_utils(self, request)


class AddCommentView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest, section: str, ids: int, flag_error: Optional[bool] = False) -> HttpResponse:
        return render(request, "forum/add_comment.html",
                      context=AddCommentViewUtils().add_comment_view_utils(section, ids, flag_error))

    def post(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        return AddCommentViewUtils().add_comment_view_post_utils(self, request, section, ids)


def some_id_view(request: HttpRequest, section: str, ids: int) -> HttpResponse:
    return render(request, "forum/some_id.html", context=SomeIdUtils().some_id_view_utils(request, section, ids))


def some_section_view(request: HttpRequest, section: str) -> HttpResponse:
    return render(request, "forum/some_header.html",
                  context=SomeSectionViewUtils().some_section_view_utils(request, section))


class SomeUserTopicsView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "forum/some_user_topics.html",
                      context=SomeUserTopicsViewUtils().some_user_topics_view_utils(request))


class DeleteTopicView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        return DeleteTopicViewUtils().delete_topic_view_utils(request, section, ids)

    def post(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        return DeleteTopicViewUtils().delete_topic_view_post_utils(request, section, ids)
