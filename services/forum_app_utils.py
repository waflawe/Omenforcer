from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from forum_app.models import Topic, Comments
from services.common_utils import get_user_avatar_path, get_crop_upload_path, RequestHost
from services.forum_mixins import *
from home_app.models import UserSettings
from forum.settings import MEDIA_ROOT
from forum_app.forms import AddTopicForm, AddCommentForm

from random import randrange
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

Username = str


@dataclass
class ExtendedSection:
    """ Датакласс с полной информации о разделе форума. """

    section: str
    section_url_alias: str
    all_topics_count: Optional[int] = None
    last_updated_time: Optional[datetime] = None
    last_updated_user: Optional[Username] = None


class ForumHomeViewUtils(BaseContextMixin):
    def forum_home_view_utils(self, request: HttpRequest) -> Context:
        context = self.get_base_context(request, get_tzone=True, forum_menu=True, view_info_menu=True)
        context["search_home"], context["sections"] = True, self._get_extended_sections()
        return context

    def _get_extended_sections(self) -> List[ExtendedSection]:
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
        action = OffsetAction("forum_app:search")
        context = self.get_search_context(request, offset_action=action, convert_objects=True)
        return context


class SomeSectionViewUtils(SearchContextMixin):
    def some_section_view_utils(self, request: HttpRequest, section: str) -> Context:
        action = OffsetAction("forum_app:some_section", section)
        context = self.get_search_context(request, offset_action=action, section=section)
        context["success_updated"] = request.GET.get("success_updated", False)
        return context


class SomeIdUtils(BaseContextMixin):
    static_context_variables = {
        "forum_menu": True,
        "add_comment_button": True,
        "queryset_context_alias": "comments",
        "view_info_menu": True,
        "get_tzone": True
    }

    def some_id_view_utils(self, request: HttpRequest, section: str, ids: int) -> Context:
        topic, section = get_topic_and_validate_section(ids, section)
        topic = TopicOrCommentObject(topic)
        topic.path_to_author_avatar, user_settings = get_user_avatar_path(topic.obj.author)
        topic = self._set_avatar_and_upload_attributes(topic, user_settings)
        topic.user_signature = user_settings.signature
        action = OffsetAction("forum_app:some_id", section, str(ids))
        context = self.get_base_context(
            request, delete=request.user == topic.obj.author, queryset=topic.obj.comments, offset_action=action,
            section=section, **self.static_context_variables
        )
        context["comments"] = self._comments_to_dict(context["offset_params"]["offset"], context["comments"])
        self._process_comments(context["comments"]) if len(context["comments"]) > 0 else None
        context["topic"], context["any_random_integer"] = topic, randrange(100000)
        context["tzone"] = user_settings.timezone
        return context

    def _process_comments(self, comments: Dict[str, TopicOrCommentObject]) -> Literal[None]:
        """
        Функция для финальной обработки комментариев (установки подписей авторов,
        путей и ссылок на их аватарки и вложения к комментарию).
        """

        authors_settings = self._set_user_signatures(comments)
        for author_settings, comment in zip(authors_settings, comments.items()):
            self._set_avatar_and_upload_attributes(comment[1], author_settings, avatar=True)

    def _set_avatar_and_upload_attributes(self, obj: TopicOrCommentObject, user_settings: UserSettings,
                                          avatar: Optional[bool] = False) -> TopicOrCommentObject:
        """
        Функция для установки атрибутов, связанных с вложением к теме/комментарию
        и аватаром автора темы/комментария.
        """

        if avatar: obj.path_to_author_avatar, _ = get_user_avatar_path(user_settings)
        if obj.obj.upload != "":
            obj.url_to_upload = obj.obj.upload.path.split(MEDIA_ROOT)[-1]
            obj.path_to_crop_upload = get_crop_upload_path(str(obj.obj.upload))
            obj.percents_of_tds_widths = PercentsOfTableData("20%", "65%", "15%")
        return obj

    def _set_user_signatures(self, comments: Dict[str, TopicOrCommentObject]) -> List[UserSettings]:
        """ Функция для установления подписей комментаторов. """

        authors = tuple(comment.obj.author for comment in comments.values())
        settings, authors_settings = UserSettings.objects.filter(user__in=authors).all(), list()
        for author in authors:
            for author_settings in settings:
                if author == author_settings.user: authors_settings.append(author_settings)
        for author_settings, comment in zip(authors_settings, comments.items()):
            comment[1].user_signature = author_settings.signature
        return authors_settings

    def _comments_to_dict(self, offset: int, comments_: QuerySet) -> Dict[str, TopicOrCommentObject]:
        comments = {}
        for position in range(offset + 1, offset + 21):
            try:
                comments[str(position)] = TopicOrCommentObject(comments_[position - 1])
            except IndexError:
                break
        return comments


class AddTopicViewUtils(AddInstanceMixin):
    validation_class = AddTopicForm

    def add_topic_view_utils(self, view_self, request: HttpRequest) -> HttpResponse:
        flag = self.add_instance(request.user, request.POST, request.FILES)
        if isinstance(flag.topic, Topic):
            url = reverse('forum_app:some_section', kwargs={'section': flag.topic.section.lower()})
            return redirect(f"{url}?success_updated=True")
        return view_self.get(request=request, flag_error=flag.comment)


class AddCommentViewUtils(AddInstanceMixin):
    validation_class = AddCommentForm

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
        if isinstance(topic, Topic) and comment:
            count = topic.comments.count()
            if not count >= 20:
                return redirect(reverse("forum_app:some_id", kwargs={"ids": ids, "section": section}))
            return redirect(f'{reverse("forum_app:some_id", kwargs={"ids": ids, "section": section})}'
                            f'?offset={count if count % 20 == 0 else self._get_valid_offset_to_redirect(count)}')
        return view_self.get(request, section, ids, flag_error=comment)

    def _get_valid_offset_to_redirect(self, count: int) -> int:
        for i in range(count, count-20, -1):
            if i % 20 == 0:
                return i


class SomeUserTopicsViewUtils(SearchContextMixin):
    def some_user_topics_view_utils(self, request: HttpRequest) -> Context:
        action = OffsetAction("forum_app:my_topics")
        context = self.get_search_context(request, offset_action=action, convert_objects=True, author=request.user)
        return context


class DeleteTopicViewUtils(DeleteTopicMixin):
    request_host = RequestHost.VIEW

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
