from django.http import HttpRequest, Http404
from django.db.models.query import QuerySet
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from forum_app.models import Topic
from forum_app.constants import dict_sections, SearchParamsExpressions
from services.common_mixins import Context, TimezoneMixin
from tasks.home_app_tasks import make_center_crop
from forum_app.models import Comments
from forum.settings import BASE_DIR, MEDIA_ROOT
from forum_app.forms import TopicForm, CommentForm

from typing import Optional, Dict, NoReturn, NamedTuple, List, Mapping, Tuple, Sized, Literal, Union
import os


class ClippedTopicsAndFlags(NamedTuple):
    clipped_topics: List
    offset_next: int
    offset_back: int
    view_buttons: bool


class SectionMixin(object):
    def validate_section(self, section: str, topic: Optional[Topic] = None) -> NoReturn | str:
        if not dict_sections.get(section, False):
            raise Http404
        if topic:
            if topic.section != section.lower():
                raise Http404
        return section.lower()


class OffsetMixin(object):
    def get_and_validate_offset(self, request: HttpRequest, instance: Sized) -> int:
        try:
            offset = int(request.GET.get("offset", 0))
            if offset % 20 != 0 or offset > len(instance) or offset < 0:
                raise Http404
        except ValueError:
            raise Http404
        return offset


class BaseContextMixin(OffsetMixin, TimezoneMixin):
    def _clip_topics_and_get_offset_params(self, request: HttpRequest, queryset: QuerySet) -> ClippedTopicsAndFlags:
        all_objects = queryset.order_by('-time_added').all()
        offset = self.get_and_validate_offset(request, all_objects)

        return ClippedTopicsAndFlags(
            all_objects[offset:offset + 20],
            offset + 20,
            offset - 20,
            len(all_objects[offset + 20:]) > 0
        )

    def get_base_context(self, request: HttpRequest, queryset: Optional[QuerySet] = None,
                         tzone: Optional[bool] = None, forum: Optional[bool] = None,
                         search: Optional[bool] = None, add_comment: Optional[bool] = None,
                         delete: Optional[bool] = None, section: Optional[str] = None,
                         search_keys: Optional[Dict] = None) -> Context:
        c = Context()
        c["search"], c["forum"], c["tzone"], c["add_comment"], c["delete"], c["section"] = \
            search, forum, self.get_timezone(request) if tzone else False, add_comment, delete, section
        if queryset:
            o_p = {}
            c["all_topics"], o_p["offset_next"], o_p["offset_back"], o_p["buttons"], o_p["search"] = \
                *self._clip_topics_and_get_offset_params(request, queryset), request.GET.get("search", False)
            c["offset_params"] = o_p
        if search_keys:
            c["search_keys"] = search_keys.keys()
        return c


class SearchMixin(SectionMixin, BaseContextMixin):
    def _get_search_filtered_queryset(self, request: HttpRequest, default_filter: Optional[Mapping] = None) -> \
            Tuple[QuerySet, Dict | None]:
        filter_kwargs = dict(default_filter)
        queryset = Topic.objects.select_related("author").filter(**filter_kwargs)
        search = request.GET.get("search", False)
        if not search:
            return queryset, None
        filter_kwargs.clear()
        for p, e in SearchParamsExpressions.Params.items():
            if request.GET.get(p, False):
                filter_kwargs[e] = search
        query = Q()
        for k, v in filter_kwargs.items():
            query = query | Q(**{f"{k}__contains": v})
        return queryset.filter(query), filter_kwargs

    def get_search_context(self, request: HttpRequest, **filters) -> Context:
        if filters.get("section", False):
            filters["section"] = self.validate_section(filters["section"])
        queryset, filtered = self._get_search_filtered_queryset(request, default_filter=filters)
        context = self.get_base_context(request, queryset=queryset, tzone=True, forum=True, search=True,
                                        section=dict_sections.get(filters.get("section", None)), search_keys=filtered)
        if queryset.count() == 0:
            context["all_topics"] = []
        return context


class DeleteTopicMixin(object):
    def delete_topic(self, topic: Topic) -> Literal[None]:
        comments = list(comment for comment in Comments.objects.filter(topic=topic).all())
        for comment in comments:
            comment.delete()
        topic.delete()


class AddInstanceMixin(object):
    def add_instance(self, user: User, post: Mapping, files: Mapping, topic_id: Optional[int] = None) -> \
            Topic | Comments | str:
        kwargs = {"author": user}
        if topic_id:
            kwargs["topic"] = get_object_or_404(Topic, pk=topic_id)
        instance = Topic.objects.create(**kwargs) if not topic_id else Comments.objects.create(**kwargs)
        form = TopicForm(post, files, instance=instance) if not topic_id else CommentForm(post, files,
                                                                                          instance=instance)
        if form.is_valid():
            obj = form.save()
            if obj.upload:
                make_center_crop.delay(obj.upload.path)
            return obj
        instance.delete()
        return form.errors
