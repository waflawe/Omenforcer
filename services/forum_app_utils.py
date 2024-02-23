from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin

from forum_app.models import Topic, Comments
from services.common_utils import get_user_avatar_path, get_crop_upload_path
from services.forum_mixins import *
from forum.settings import MEDIA_ROOT
from forum_app.forms import AddTopicForm, AddCommentForm

from random import randrange
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ExtendedSection:
    """ Датакласс с полной информации о секции форума. """

    section: str
    section_url_alias: str
    all_topics_count: Optional[int] = None
    last_updated_time: Optional[datetime] = None
    last_updated_user: Optional[str] = None


class ForumHomeViewUtils(BaseContextMixin):
    def forum_home_view_utils(self, request: HttpRequest) -> Context:
        context = self.get_base_context(request, get_tzone=True, forum_menu=True)
        context["search_home"], context["sections"] = True, self._get_sections()
        return context

    def _get_sections(self) -> List[ExtendedSection]:
        sections = []
        for url_alias, name in dict_sections.items():
            section = ExtendedSection(name, url_alias)
            section.all_topics_count = Topic.objects.filter(section=section.section_url_alias).count()
            last_topic = (Topic.objects.select_related("author").only("time_added", "author__username")
                          .filter(section=section.section_url_alias).first())
            if last_topic:
                section.last_updated_time, section.last_updated_user = last_topic.time_added, last_topic.author.username
            sections.append(section)
        return sections


class SearchViewUtils(SearchContextMixin):
    def search_view_utils(self, request: HttpRequest) -> Context:
        context = self.get_search_context(request, convert_objects=True)
        return context


class SomeSectionViewUtils(SearchContextMixin):
    def some_section_view_utils(self, request: HttpRequest, section: str) -> Context:
        context = self.get_search_context(request, section=section)
        context["success_updated"] = request.GET.get("success_updated", False)
        context["dont_have_required_permissions"] = request.GET.get("dont_have_required_permissions", False)
        return context


class SomeIdUtils(BaseContextMixin):
    static_context_variables = {
        "forum_menu": True,
        "add_comment": True,
        "queryset_context_alias": "comments"
    }

    def some_id_view_utils(self, request: HttpRequest, section: str, ids: int) -> Context:
        topic, section = self._get_topic_and_validate_section(section, ids)
        topic, user_settings = self._set_time_and_avatar_attributes(topic, return_settings=True)
        context = self.get_base_context(
            request, delete=request.user == topic.obj.author, section=section, queryset=topic.obj.comments,
            **self.static_context_variables
        )
        context["comments"] = self._get_offset_comments(context["offset_params"]["offset_next"]-20,
                                                        context["comments"]) if len(context["comments"]) > 0 else None
        context["topic"], context["any_random_integer"] = topic, randrange(100000)
        context["tzone"] = user_settings.timezone
        return context

    def _get_topic_and_validate_section(self, section: str, ids: int) -> Tuple[TopicOrCommentObject, str]:
        try:
            topic = (Topic.objects.select_related("author").only
                     ("title", "question", "time_added", "upload", "author", "section", "views").get(pk=ids))
        except ObjectDoesNotExist:
            raise Http404
        topic = TopicOrCommentObject(topic)
        section = validate_section(section, topic.obj)
        topic.obj.views = F("views") + 1
        topic.obj.save(update_fields=["views"])
        return topic, section

    def _get_offset_comments(self, offset: int, comments: QuerySet[Comments]) -> Dict:
        comments = tuple(self._set_time_and_avatar_attributes(TopicOrCommentObject(comment)) for comment in comments)
        return self._comments_to_dict(offset, comments)

    def _set_time_and_avatar_attributes(self, obj: TopicOrCommentObject, return_settings: bool = False) \
            -> TopicOrCommentObject | Tuple:
        obj.path_to_avatar, user_settings = get_user_avatar_path(obj.obj.author)
        if obj.obj.upload != "":
            obj.url_to_upload = obj.obj.upload.path.split(MEDIA_ROOT)[-1]
            obj.path_to_crop_upload = get_crop_upload_path(str(obj.obj.upload))
            obj.percents_of_tds_widths = PercentsOfTableData("20%", "65%", "15%")
        return obj if not return_settings else (obj, user_settings)

    def _comments_to_dict(self, offset: int, comments_: Tuple) -> Dict:
        comments = {}
        for position in range(offset + 1, offset + 21):
            try:
                comments[str(position)] = comments_[position - 1]
            except IndexError:
                break
        return comments


class AddTopicViewUtils(AddInstanceMixin, LoginRequiredMixin):
    validation_class = AddTopicForm
    login_url = reverse_lazy("home_app:auth")

    def add_topic_view_utils(self, view_self, request: HttpRequest) -> HttpResponse:
        topic, _ = self.add_instance(request.user, request.POST, request.FILES)
        if isinstance(topic, Topic):
            return redirect(f"{reverse('forum_app:some_section', kwargs={'section': topic.section.lower()})}"
                            f"?success_updated=True")
        return view_self.get(request=request, flag_error=True)


class AddCommentViewUtils(AddInstanceMixin, LoginRequiredMixin):
    validation_class = AddCommentForm
    login_url = reverse_lazy("home_app:auth")

    def add_comment_view_utils(self, section: str, ids: int, flag_error: bool) -> Context:
        topic = get_object_or_404(Topic, pk=ids)
        section = validate_section(section, topic)
        return Context({
            "form": self.validation_class(),
            "flag_error": flag_error,
            "section": section
        })

    def add_comment_view_post_utils(self, view_self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        topic, comment = self.add_instance(request.user, request.POST, request.FILES, topic=ids, section=section)
        if comment:
            count = topic.comments.count()
            if not count >= 20:
                return redirect(reverse("forum_app:some_id", kwargs={"ids": ids, "section": section}))
            return redirect(f'{reverse("forum_app:some_id", kwargs={"ids": ids, "section": section})}'
                            f'?offset={count if count % 20 == 0 else self._get_valid_offset_to_redirect(count)}')
        return view_self.get(request, section, ids, flag_error=True)

    def _get_valid_offset_to_redirect(self, count: int) -> int:
        for i in range(count, count-20, -1):
            if i % 20 == 0:
                return i


class SomeUserTopicsViewUtils(SearchContextMixin):
    def some_user_topics_view_utils(self, request: HttpRequest) -> Context:
        context = self.get_search_context(request, convert_objects=True, author=request.user)
        return context


class DeleteTopicViewUtils(DeleteTopicMixin, LoginRequiredMixin):
    login_url = reverse_lazy("home_app:auth")

    def delete_topic_view_utils(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        topic = self.check_perms(request, ids, section)
        return render(request, "forum/delete.html", context={
            "ids": ids,
            "topic": topic,
            "forum": True
        })

    def delete_topic_view_post_utils(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        self.delete_topic(request, ids, section)
        return redirect(f"{reverse('forum_app:some_section', kwargs={'section': section})}"
                        f"?success_updated=True")
