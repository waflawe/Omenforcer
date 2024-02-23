from django.http import HttpRequest, Http404
from django.db.models.query import QuerySet
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from forum_app.models import Topic
from forum_app.constants import dict_sections, SearchParamsExpressions
from services.common_utils import Context, DataValidationMixin, get_timezone
from tasks.home_app_tasks import make_center_crop
from forum_app.models import Comments

from typing import Optional, NoReturn, NamedTuple, List, Tuple, Sized, Literal, Iterable, Dict
from dataclasses import dataclass


class PercentsOfTableData(NamedTuple):
    """
    Кортеж для хранения информации о ширине 'td' HTML тэгов.
    Используется для красивого отображения заголовков тем и комментариев.
    """

    one_data: str = "20%"
    two_data: str = "80%"
    three_data: Optional[str] = False


@dataclass
class TopicOrCommentObject:
    """ Датакласс для хранения всей нужной для рендеринга информации о заголовке темы или комментарие. """

    obj: Topic | Comments
    path_to_author_avatar: Optional[str] = None
    url_to_upload: Optional[str] = None
    path_to_crop_upload: Optional[str] = None
    percents_of_tds_widths: PercentsOfTableData = PercentsOfTableData()
    section: Optional[str] = None


class StripedObjectsAndFlags(NamedTuple):
    objects: List
    offset_next: int
    offset_back: int
    buttons: bool


def validate_section(section: str, topic: Optional[Topic] = None) -> NoReturn | str:
    if not dict_sections.get(section, False):
        raise Http404
    if topic:
        if topic.section != section.lower():
            raise Http404
    return section.lower()


def get_and_validate_offset(request: HttpRequest, instance: Sized) -> int:
    try:
        offset = int(request.GET.get("offset", 0))
        if offset % 20 != 0 or offset > len(instance) or offset < 0:
            offset = 0
    except ValueError:
        offset = 0
    return offset


class BaseContextMixin(object):
    """ Класс для быстрого формирования базового контекста. """

    static_base_context_variables = {
        "view_search_form": "search_form",
        "view_forum_menu": "forum_menu",
        "view_link_on_add_comment_page": "view_link_on_add_comment_page",
        "view_delete_button": "delete",
        "section": "section",
        "view_add_comment_button": "add_comment",
        "search_keys": "search_keys"
    }

    def get_base_context(self, request: HttpRequest, **kwargs) -> Context:
        context, queryset = Context(offset_params={}), kwargs.get("queryset", False)
        for template_name, arg_name in self.static_base_context_variables.items():
            context[template_name] = kwargs.get(arg_name)
        if kwargs.get("get_tzone", False):
            context["tzone"] = get_timezone(request)
        if not queryset is False:
            objects, offset_next, offset_back, buttons = self._clip_topics_and_get_offset_params(request, queryset)
            context[kwargs["queryset_context_alias"]] = objects if len(objects) > 0 else tuple()
            context["offset_params"]["offset_next"] = offset_next
            context["offset_params"]["offset_back"], context["offset_params"]["buttons"] = offset_back, buttons
            context["offset_params"]["search"] = request.GET.get("search", False)
        return context

    def _clip_topics_and_get_offset_params(self, request: HttpRequest, queryset: QuerySet) -> StripedObjectsAndFlags:
        offset = get_and_validate_offset(request, queryset)
        return StripedObjectsAndFlags(
            queryset[offset:offset + 20],
            offset + 20,
            offset - 20,
            len(queryset[offset + 20:]) > 0
        )


class SearchContextMixin(BaseContextMixin):
    """ Класс для быстрого формирования базового контекста для страниц, поддерживающих поиск. """

    static_search_context_variables = {
        "get_tzone": True,
        "forum_menu": True,
        "search_form": True,
        "queryset_context_alias": "all_topics"
    }

    def _get_search_query(self, request: HttpRequest) -> Tuple[Q, Iterable]:
        search = request.GET.get("search", False)
        if not search:
            return Q(), tuple()
        filter_kwargs = {e: search for p, e in SearchParamsExpressions.Params.items() if request.GET.get(p, False)}
        query = Q()
        for k, v in filter_kwargs.items():
            query = query | Q(**{f"{k}__icontains": v})
        return query, filter_kwargs.keys()

    def get_search_context(self, request: HttpRequest, convert_objects: bool = False, **filters) -> Context:
        if filters.get("section", False):
            filters["section"] = validate_section(filters["section"])
        query, filter_keys = self._get_search_query(request)
        queryset = (Topic.objects.select_related("author").only
                    ("title", "section", "views", "time_added", "author__username").filter(**filters).filter(query))
        context = self.get_base_context(
            request, queryset=queryset, section=dict_sections.get(filters.get("section", None)),
            search_keys=filter_keys, **self.static_search_context_variables
        )
        if len(context["all_topics"]) > 0 and convert_objects:
            context["all_topics"] = tuple(TopicOrCommentObject(topic, section=dict_sections[topic.section])
                                          for topic in context["all_topics"])
        return context


class DeleteTopicMixin(object):
    """ Миксин для удаления темы. """

    def delete_topic(self, request: HttpRequest, ids: int, section: Optional[str] = None) -> Literal[None]:
        topic = self.check_perms(request, ids, section)
        for comment in topic.comments:
            comment.delete()
        topic.delete()

    def check_perms(self, request: HttpRequest, ids: int, section: Optional[str] = None) -> Topic | NoReturn:
        topic = get_object_or_404(Topic, pk=ids)
        if section:
            validate_section(section, topic)
        if topic.author == request.user or request.user.is_superuser():
            return topic
        raise PermissionDenied


class AddInstanceMixin(DataValidationMixin):
    """ Миксин для добавления темы или комментария. """

    AddInstanceReturn = Tuple[Topic, Literal[None]] | Tuple[Topic, Comments] | Tuple[False, False]

    def add_instance(self, user: User, post: Dict, files: Dict, topic: Optional[int] = None,
                     section: Optional[str] = None) -> AddInstanceReturn:
        kwargs = self._get_and_validate_instance_kwargs(user, topic, section)
        if not kwargs: return False, False
        instance = Topic.objects.create(**kwargs) if not topic else Comments.objects.create(**kwargs)
        v, is_valid, data = self.validate_received_data(post, files, instance)

        if is_valid:
            instance = v.save()
            if instance.upload:
                make_center_crop.delay(instance.upload.path)
            return (instance, None) if not topic else (kwargs["topic"], instance)
        return False, False

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:
        return data

    def _get_and_validate_instance_kwargs(self, user: User, topic: int | None, section: str | None) \
            -> Literal[False] | Dict:
        kwargs = {"author": user}
        if topic:
            try:
                kwargs["topic"] = get_object_or_404(Topic, pk=int(topic))
            except (ValueError, Http404):
                return False
            if section: validate_section(section, kwargs["topic"])
        return kwargs
