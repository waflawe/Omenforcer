from django.http import HttpRequest, Http404
from django.db.models.query import QuerySet
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from forum_app.models import Topic, Comment
from forum_app.constants import dict_sections, SearchParamsExpressions
from services.common_utils import Context
from services.schemora.mixins import DataValidationMixin, RequestHost
from services.schemora.settings import get_user_settings_model
from tasks.home_app_tasks import make_center_crop
from error_messages.forum_error_messages import TOPICS_ERRORS, COMMENTS_ERRORS, ErrorMessage

from typing import Optional, NoReturn, NamedTuple, Tuple, Sized, Literal, Iterable, Dict
from dataclasses import dataclass

ReverseURL = str
UserSettings = get_user_settings_model()


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

    obj: Topic | Comment
    path_to_author_avatar: str = None
    url_to_upload: Optional[str] = None
    path_to_crop_upload: Optional[str] = None
    percents_of_tds_widths: PercentsOfTableData = PercentsOfTableData()
    section: Optional[str] = None
    user_signature: str = None


class OffsetButton(NamedTuple):
    """ Класс для хранения нужной HTML кнопке переключения оффсета информации. """

    offset: int
    view_button: bool

    def __str__(self):
        return str(self.offset)

    def __sub__(self, other):
        return self.offset - other


class ObjectsAndOffsets(NamedTuple):
    objects: QuerySet
    offset: int
    offset_next: OffsetButton
    offset_back: OffsetButton


class AddInstanceReturn(NamedTuple):
    topic: Topic | Literal[None]
    comment: Literal[None] | Comment | ErrorMessage


class OffsetAction(NamedTuple):
    offset_action: ReverseURL
    offset_action_param1: Optional[str] = None
    offset_action_param2: Optional[str] = None


def get_timezone(request: HttpRequest) -> Literal[False] | str:
    if request.user.is_authenticated:
        return UserSettings.objects.get(user=request.user).timezone
    return False


def validate_section(section: str, topic: Optional[Topic] = None, raise_exception: bool = True) -> NoReturn | str:
    """ Функция для проверки соответствия переданной секции форума с секцией конкретной темы. """

    if (not dict_sections.get(section, False)) or (topic and topic.section != section.lower()):
        if raise_exception:
            raise Http404
        return False
    return section.lower()


def get_topic_and_validate_section(ids: int, section: Optional[str] = None) -> Tuple[Topic, str]:
    """ Функция для получения темы по ее ids и проверки ее секции на соответствие секции, переданной пользователем. """

    topic_fields = "id", "title", "question", "time_added", "upload", "author", "section", "views"
    topic_q = Topic.objects.select_related("author").only(*topic_fields).filter(pk=ids)
    topic = topic_q.first()
    if not topic:
        raise Http404
    if section:
        section = validate_section(section, topic)
    topic_q.update(views=F("views")+1)
    return topic, section


def get_and_validate_offset(request: HttpRequest, instance: Sized) -> int:
    """ Функция для проверки переданного оффсета. """

    try:
        offset = int(request.GET.get("offset", 0))
        if offset % 20 != 0 or offset >= len(instance) or offset < 0:
            offset = 0
    except ValueError:
        offset = 0
    return offset


class BaseContextMixin(object):
    """ Класс для удобного формирования базового контекста. """

    static_base_context_variables = {
        "view_search_form": "search_form",
        "view_forum_menu": "forum_menu",
        "view_delete_button": "delete",
        "section": "section",
        "view_add_comment_button": "add_comment_button",
        "search_keys": "search_keys"
    }

    def get_base_context(self, request: HttpRequest, **kwargs) -> Context:
        context, queryset = Context(offset_params={}), kwargs.get("queryset", False)
        for template_name, arg_name in self.static_base_context_variables.items():
            context[template_name] = kwargs.get(arg_name)
        if kwargs.get("get_tzone", False):
            context["tzone"] = get_timezone(request)
        if kwargs.get("view_info_menu", False):
            context["view_info_menu"], context["last_joined"] = True, User.objects.order_by("-date_joined").first()
            context["tzone"] = "UTC" if context["tzone"] in ("Default", False) else context["tzone"]
            context["total_topics"] = Topic.objects.count()
            context["total_messages"] = context["total_topics"] + Comment.objects.count()
        if not queryset is False:
            objects, offset, offset_next, offset_back = self._clip_topics_and_get_offset_params(request, queryset)
            context[kwargs["queryset_context_alias"]] = objects if len(objects) > 0 else tuple()
            context["offset_params"]["offset_next"], context["offset_params"]["offset"] = offset_next, offset
            context["offset_params"]["offset_back"] = offset_back
            context["offset_params"]["search"] = request.GET.get("search", False)
            action = kwargs["offset_action"]
            context["offset_action"] = action
        return context

    def _clip_topics_and_get_offset_params(self, request: HttpRequest, queryset: QuerySet) -> ObjectsAndOffsets:
        offset = get_and_validate_offset(request, queryset)
        return ObjectsAndOffsets(
            queryset,
            offset,
            OffsetButton(offset + 20, len(queryset[offset + 20:]) > 0),
            OffsetButton(offset - 20, len(queryset[:offset]) > 0),
        )


class SearchContextMixin(BaseContextMixin):
    """ Класс для удобного формирования базового контекста для страниц, поддерживающих поиск. """

    static_search_context_variables = {
        "get_tzone": True,
        "forum_menu": True,
        "search_form": True,
        "queryset_context_alias": "all_topics",
        "view_info_menu": True
    }

    def _get_search_query(self, request: HttpRequest) -> Tuple[Q, Iterable]:
        search = request.GET.get("search", False)
        if not search:
            return Q(), tuple()
        filter_kwargs = {f: search for p, f in SearchParamsExpressions.Params.items() if request.GET.get(p, False)}
        query = Q()
        for f, q in filter_kwargs.items():
            query = query | Q(**{f"{f}__icontains": q})
        return query, filter_kwargs.keys()

    def get_search_context(self, request: HttpRequest, offset_action: OffsetAction, convert_objects: bool = False,
                           **base_topic_filters) -> Context:
        if base_topic_filters.get("section", False):
            base_topic_filters["section"] = validate_section(base_topic_filters["section"])
        query, filter_keys = self._get_search_query(request)
        fields = "title", "section", "views", "time_added", "author__username"
        queryset = Topic.objects.select_related("author").only(*fields).filter(**base_topic_filters).filter(query)
        context = self.get_base_context(
            request, queryset=queryset, section=dict_sections.get(base_topic_filters.get("section", None)),
            search_keys=filter_keys, offset_action=offset_action, **self.static_search_context_variables
        )
        offset, offset_next = context["offset_params"]["offset"], context["offset_params"]["offset_next"].offset
        context["all_topics"] = context["all_topics"][offset:offset_next]
        context["all_topics_count"] = len(context["all_topics"])
        if context["all_topics_count"] > 0 and convert_objects:
            context["all_topics"] = tuple(TopicOrCommentObject(topic, section=dict_sections[topic.section])
                                          for topic in context["all_topics"])
        return context

    # Как тут сделать сортировку?..
    # def _get_and_validate_sort(self, request: HttpRequest) -> Literal[False] | str:
    #     sort = request.GET.get("sort", False)
    #     if sort and sort == "time_updated":
    #         return "time_updated"
    #     return False


class DeleteTopicMixin(object):
    """ Миксин для удаления темы. """

    def delete_topic(self, request: HttpRequest, ids: int, section: Optional[str] = None) -> Literal[None] | NoReturn:
        topic = self.check_perms(request, ids, section)
        for comment in topic.comments:
            comment.delete()
        topic.delete()

    def check_perms(self, request: HttpRequest, ids: int, section: Optional[str] = None) -> Topic | NoReturn | False:
        topic = get_object_or_404(Topic, pk=ids)
        if section:
            validate_section(section, topic)
        if topic.author == request.user or request.user.is_superuser:
            return topic
        raise PermissionDenied


class AddInstanceMixin(DataValidationMixin):
    """ Миксин для добавления темы или комментария. """

    request_host = None   # переменная-источник запроса. Имеет значение RequestHost.APIVIEW или RequestHost.VIEW

    def add_instance(self, user: User, post: Dict, files: Dict, topic: Optional[int] = None,
                     section: Optional[str] = None) -> AddInstanceReturn:
        kwargs = self._get_and_validate_kwargs(user, topic, section)
        if isinstance(kwargs, ErrorMessage): return AddInstanceReturn(None, kwargs)
        instance = Topic.objects.create(**kwargs) if not topic else Comment.objects.create(**kwargs)
        v, is_valid, data = self.validate_received_data(post, files, instance)

        if is_valid:
            instance = v.save()
            if instance.upload:
                make_center_crop.delay(instance.upload.path)
            return AddInstanceReturn(*((instance, None) if not topic else (kwargs["topic"], instance)))
        return self._get_error_return(instance, v, topic)

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:
        return data

    def _get_and_validate_kwargs(self, user: User, topic: Optional[int] = None, section: Optional[str] = None) \
            -> ErrorMessage | Dict:
        kwargs = {"author": user}
        if not topic:
            return kwargs
        try:
            kwargs["topic"] = get_object_or_404(Topic, pk=int(topic))
        except (ValueError, Http404):
            return TOPICS_ERRORS["id"]
        if section:
            flag = validate_section(section, kwargs["topic"])
            if not flag: return TOPICS_ERRORS["section"]
        return kwargs

    def _get_error_return(self, instance: Topic | Comment, v, topic: Optional[int] = None) -> AddInstanceReturn:
        instance.delete()
        is_view = self.request_host == RequestHost.VIEW
        error_field = list(v.errors.as_data().keys())[0] if is_view else v.errors.popitem(last=False)[0]
        return AddInstanceReturn(None, (TOPICS_ERRORS[error_field] if not topic else COMMENTS_ERRORS[error_field]))
