from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from forum_app.forms import AddTopicForm
from services.forum_app_utils import (
    AddCommentViewUtils,
    AddTopicViewUtils,
    DeleteTopicViewUtils,
    ForumHomeViewUtils,
    SearchViewUtils,
    SomeIdUtils,
    SomeSectionViewUtils,
    SomeUserTopicsViewUtils,
)


def forum_home_view(request: HttpRequest) -> HttpResponse:
    context = ForumHomeViewUtils().forum_home_view_utils(request)
    return render(request, "forum/home.html", context=context)


def search_view(request: HttpRequest) -> HttpResponse:
    context = SearchViewUtils().search_view_utils(request)
    return render(request, "forum/search.html", context=context)


class AddTopicView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest, flag_error: Optional[bool] = False) -> HttpResponse:
        context = {
            "form": AddTopicForm(),
            "flag_error": flag_error,
            "forum": True
        }
        return render(request, "forum/add_topic.html", context=context)

    def post(self, request: HttpRequest) -> HttpResponse:
        return AddTopicViewUtils().add_topic_view_utils(self, request)


class AddCommentView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest, section: str, ids: int, flag_error: Optional[bool] = False) -> HttpResponse:
        context = AddCommentViewUtils().add_comment_view_utils(section, ids, flag_error)
        return render(request, "forum/add_comment.html", context=context)

    def post(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        return AddCommentViewUtils().add_comment_view_post_utils(self, request, section, ids)


def some_id_view(request: HttpRequest, section: str, ids: int) -> HttpResponse:
    context = SomeIdUtils().some_id_view_utils(request, section, ids)
    return render(request, "forum/some_id.html", context=context)


def some_section_view(request: HttpRequest, section: str) -> HttpResponse:
    context = SomeSectionViewUtils().some_section_view_utils(request, section)
    return render(request, "forum/some_header.html", context=context)


class SomeUserTopicsView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest) -> HttpResponse:
        context = SomeUserTopicsViewUtils().some_user_topics_view_utils(request)
        return render(request, "forum/some_user_topics.html", context=context)


class DeleteTopicView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home_app:auth")

    def get(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        return DeleteTopicViewUtils().delete_topic_view_utils(request, section, ids)

    def post(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        return DeleteTopicViewUtils().delete_topic_view_post_utils(request, section, ids)
