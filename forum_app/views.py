from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.views import View

from services.common_mixins import AuthenticationMixin
from services.forum_app_utils import *
from .forms import *

from typing import Optional


def forum_home_view(request: HttpRequest) -> HttpResponse:
    return render(request, "forum/home.html", context=ForumHomeViewUtils().forum_home_view_utils(request))


def search_view(request: HttpRequest) -> HttpResponse:
    return render(request, "forum/search.html", context=SearchViewUtils().search_view_utils(request))


class AddTopicView(View):
    def get(self, request: HttpRequest, flag_error: Optional[bool] = False) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request):
            return render(request, "forum/add_topic.html", context={
                "form": TopicForm(),
                "flag_error": flag_error,
                "forum": True
            })

        return redirect(reverse("home_app:auth"))

    def post(self, request: HttpRequest) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request):
            return AddTopicViewUtils().add_topic_view_utils(self, request)

        return redirect(reverse("home_app:auth"))


class AddCommentView(View):
    def get(self, request: HttpRequest, section: str, ids: int, flag_error: Optional[bool] = False) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request):
            return render(request, "forum/add_comment.html",
                          context=AddCommentViewUtils().add_comment_view_utils(section, ids, flag_error))

        return redirect(reverse("home_app:auth"))

    def post(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request):
            return AddCommentViewUtils().add_comment_view_post_utils(self, request, section, ids)

        return redirect(reverse("home_app:auth"))


def some_id_view(request: HttpRequest, section: str, ids: int) -> HttpResponse:
    return render(request, "forum/some_id.html", context=SomeIdUtils().some_id_view_utils(request, section, ids))


def some_section_view(request: HttpRequest, section: str) -> HttpResponse:
    return render(request, "forum/some_header.html",
                  context=SomeSectionViewUtils().some_section_view_utils(request, section))


class SomeUserTopicsView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if AuthenticationMixin().check_is_user_auth(request):
            return render(request, "forum/some_user_topics.html",
                          context=SomeUserTopicsViewUtils().some_user_topics_view_utils(request))

        return redirect(reverse("home_app:auth"))


class DeleteTopicView(View):
    def get(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        return DeleteTopicViewUtils().delete_topic_view_utils(request, section, ids)

    def post(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        return DeleteTopicViewUtils().delete_topic_view_post_utils(request, section, ids)
