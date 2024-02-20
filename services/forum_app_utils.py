from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist

from forum_app.models import Topic, Comments
from .common_mixins import *
from forum_app.forms import *
from .forum_mixins import *

from random import randrange
from copy import deepcopy
from datetime import datetime
from typing import NamedTuple, Literal, List, Dict, Tuple, Optional
from dataclasses import dataclass


class PercentsOfTableData(NamedTuple):
    one_data: str = "20%"
    two_data: str = "80%"
    three_data: Optional[str] = False


@dataclass
class TopicOrCommentObject:
    obj: Topic | Comments
    path_to_avatar: Optional[str] = None
    url_to_upload: Optional[str] = None
    path_to_crop_upload: Optional[str] = None
    percents_of_table_data: PercentsOfTableData = PercentsOfTableData()
    section: Optional[str] = None


@dataclass
class ExtendedSection:
    section: str
    section_url_name: str
    all_topics_count: Optional[int] = None
    last_updated_time: Optional[datetime] = None
    last_updated_user: Optional[str] = None


class ForumHomeViewUtils(BaseContextMixin):
    def forum_home_view_utils(self, request: HttpRequest) -> Context:
        context = self.get_base_context(request, tzone=True, forum=True)
        context["search_home"], context["sections"] = True, self._get_sections()
        return context

    def _get_sections(self) -> List[ExtendedSection]:
        sections = [ExtendedSection(value, key) for key, value in dict_sections.items()]
        for section in sections:
            section_topics = Topic.objects.select_related("author").filter(section=section.section_url_name)
            section.all_topics_count = section_topics.count()
            try:
                last_topic = section_topics.order_by("-time_added")[0]
            except IndexError:
                continue
            section.last_updated_time, section.last_updated_user = last_topic.time_added, last_topic.author.username
        return sections


class SearchViewUtils(SearchMixin):
    def search_view_utils(self, request: HttpRequest) -> Context:
        context = self.get_search_context(request)
        context["all_topics"] = [TopicOrCommentObject(topic) for topic in context["all_topics"]]
        for topic in context["all_topics"]:
            topic.section = dict_sections[topic.obj.section]
        return context


class SomeSectionViewUtils(SearchMixin):
    def some_section_view_utils(self, request: HttpRequest, section: str) -> Context:
        context = self.get_search_context(request, section=section)
        context["success_updated"] = request.GET.get("success_updated", False)
        context["dont_have_required_permissions"] = request.GET.get("dont_have_required_permissions", False)
        return context


class SomeIdUtils(BaseContextMixin, SectionMixin, UserAvatarMixin):
    def some_id_view_utils(self, request: HttpRequest, section: str, ids: int) -> Context:
        topic, section = self._get_topic_and_validate_section(section, ids)
        cmmnts = list(
            TopicOrCommentObject(comment)
            for comment in Comments.objects.select_related("author").filter(topic=topic.obj).all()
        )
        self._set_time_and_avatar_attributes(topic)
        comments, offset = self._get_offset_comments(request, cmmnts)
        context = self.get_base_context(request, forum=True, add_comment=True, delete=request.user == topic.obj.author,
                                        section=section, tzone=True)
        context["topic"], context["comments"], context["any_random_integer"] = topic, comments, randrange(100000)
        context["offset_params"] = dict(offset_next=offset + 20, offset_back=offset - 20,
                                        buttons=len(cmmnts[offset + 20:]) > 0)
        return context

    def _get_topic_and_validate_section(self, section: str, ids: int) -> Tuple[TopicOrCommentObject, str]:
        try:
            topic = Topic.objects.select_related("author").get(pk=ids)
        except ObjectDoesNotExist:
            raise Http404
        topic = TopicOrCommentObject(topic)
        section = self.validate_section(section, topic.obj)
        topic.obj.views = F("views") + 1
        topic.obj.save(update_fields=["views"])
        return topic, section

    def _get_offset_comments(self, request: HttpRequest, comments: List[TopicOrCommentObject]) -> Tuple[Dict, int]:
        offset = self.get_and_validate_offset(request, comments)
        new_comments = deepcopy(comments)
        for comment in new_comments[offset:offset + 20]:
            self._set_time_and_avatar_attributes(comment)
        return self._comments_to_dict(offset, new_comments), offset

    def _set_time_and_avatar_attributes(self, obj: TopicOrCommentObject) -> Literal[None]:
        obj.path_to_avatar = self.get_user_avatar_path(obj.obj.author)
        if obj.obj.upload != "":
            obj.url_to_upload = obj.obj.upload.path.split("media")[-1][1:]
            t = obj.obj.upload.path.split("media/")[-1].split(".")
            obj.path_to_crop_upload = t[0] + "_crop." + t[1]
            obj.percents_of_table_data = PercentsOfTableData("20%", "65%", "15%")

    def _comments_to_dict(self, offset: int, new_comments: List) -> Dict:
        comments = {}
        for position in range(offset + 1, offset + 21):
            try:
                comments[str(position)] = new_comments[position - 1]
            except IndexError:
                break
        return comments


class AddTopicViewUtils(AddInstanceMixin):
    def add_topic_view_utils(self, view_self, request: HttpRequest) -> HttpResponse:
        topic = self.add_instance(request.user, request.POST, request.FILES)
        if isinstance(topic, Topic):
            return redirect(f"{reverse('forum_app:some_section', kwargs={'section': topic.section.lower()})}"
                            f"?success_updated=True")
        return view_self.get(request=request, flag_error=True)


class AddCommentViewUtils(SectionMixin, AddInstanceMixin):
    def add_comment_view_utils(self, section: str, ids: int, flag_error: bool) -> Context:
        topic = get_object_or_404(Topic, pk=ids)
        section = self.validate_section(section, topic)
        return Context({
            "form": CommentForm(),
            "flag_error": flag_error,
            "section": section
        })

    def add_comment_view_post_utils(self, view_self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        topic = get_object_or_404(Topic, pk=ids)
        section = self.validate_section(section, topic)
        comment = self.add_instance(request.user, request.POST, request.FILES, topic_id=ids)
        if isinstance(comment, Comments):
            count = Comments.objects.filter(topic=topic).count()
            if not count >= 20:
                return redirect(reverse("forum_app:some_id", kwargs={"ids": ids, "section": section}))
            return redirect(f'{reverse("forum_app:some_id", kwargs={"ids": ids, "section": section})}'
                            f'?offset={count if count % 20 == 0 else self._get_valid_offset_to_redirect(count)}')
        return view_self.get(request, section, ids, flag_error=True)

    def _get_valid_offset_to_redirect(self, count: int) -> int:
        for i in range(count, count-20, -1):
            if i % 20 == 0:
                return i


class SomeUserTopicsViewUtils(SearchMixin):
    def some_user_topics_view_utils(self, request: HttpRequest) -> Context:
        context = self.get_search_context(request, author=request.user)
        try:
            context["all_topics"] = [TopicOrCommentObject(topic) for topic in context["all_topics"]]
            for topic in context["all_topics"]:
                topic.section = dict_sections[topic.obj.section]
        except KeyError:
            context["all_topics"] = []
        return context


class DeleteTopicViewUtils(SectionMixin, AuthenticationMixin, DeleteTopicMixin):
    def delete_topic_view_utils(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        if self.check_is_user_auth(request):
            topic = get_object_or_404(Topic, pk=ids)
            section = self.validate_section(section, topic)
            if topic.author == request.user:
                return render(request, "forum/delete.html", context={
                    "ids": ids,
                    "topic": topic,
                    "forum": True
                })

            return redirect(f'{reverse("forum_app:some_section", kwargs={"section": section})}'
                            f'?dont_have_required_permissions=True')

        return redirect(reverse("home_app:auth"))

    def delete_topic_view_post_utils(self, request: HttpRequest, section: str, ids: int) -> HttpResponse:
        if self.check_is_user_auth(request):
            topic = get_object_or_404(Topic, pk=ids)
            section = self.validate_section(section, topic)
            if topic.author == request.user:
                self.delete_topic(topic)
                return redirect(f"{reverse('forum_app:some_section', kwargs={'section': section})}"
                                f"?success_updated=True")

            return redirect(f'{reverse("forum_app:some_section", kwargs={"section": section})}'
                            f'?dont_have_required_permissions=True')

        return redirect(reverse("home_app:auth"))
