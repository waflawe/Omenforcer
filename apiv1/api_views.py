from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, extend_schema_view

from forum_app.models import Topic
from apiv1.serializers import (
    UserSerializer, TopicsSerializer, CommentSerializer, TopicDetailSerializer, SectionsSerializer,
    DefaultErrorSerializer, UpdateSettingsSerializer
)
from forum_app.constants import dict_sections
from apiv1.filters import TopicsSearchFilter
from services.forum_mixins import DeleteTopicMixin, AddInstanceMixin, get_topic_and_validate_section
from services.home_mixins import (
    UpdateSettingsMixin, AddReviewMixin, DropReviewMixin, get_rating_operation_error_message
)
from services.home_app_utils import check_flag
from services.schemora.mixins import RequestHost
from services.schemora.settings import get_user_settings_model
from error_messages.forum_error_messages import TOPICS_ERRORS

from typing import Optional, NamedTuple

UserSettings = get_user_settings_model()
review_operations_responses = {
    status.HTTP_201_CREATED: None,
    status.HTTP_400_BAD_REQUEST: DefaultErrorSerializer,
    status.HTTP_401_UNAUTHORIZED: DefaultErrorSerializer,
    status.HTTP_403_FORBIDDEN: DefaultErrorSerializer,
    status.HTTP_404_NOT_FOUND: DefaultErrorSerializer
}


class GetSectionsAPIView(APIView):
    @extend_schema(responses={
        status.HTTP_200_OK: SectionsSerializer
    })
    def get(self, request: Request) -> Response:
        """ Возвращает все секции форума. """
        
        return Response({"sections": dict_sections})


class TopicViewSet(GenericViewSet, mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, DeleteTopicMixin, AddInstanceMixin):
    """ Вьюсет для отображения всех, отображения одной, удаления, создания тем на форуме. """

    queryset = Topic.objects.all()
    lookup_url_kwarg = "ids"
    serializer_class = TopicsSerializer

    filter_backends = (TopicsSearchFilter,)
    search_fields = "title", "question", "author__username"
    permission_classes = (IsAuthenticatedOrReadOnly,)

    request_host = RequestHost.APIVIEW
    serializer_detail_class = TopicDetailSerializer
    validation_class = TopicDetailSerializer

    @extend_schema(responses={
        status.HTTP_200_OK: serializer_detail_class,
        status.HTTP_400_BAD_REQUEST: DefaultErrorSerializer,
        status.HTTP_404_NOT_FOUND: DefaultErrorSerializer
    })
    def retrieve(self, request, *args, **kwargs) -> Response:
        """ Получение темы по ее id. """

        if self.kwargs[self.lookup_url_kwarg].isnumeric():
            topic, _ = get_topic_and_validate_section(int(self.kwargs[self.lookup_url_kwarg]))
            return Response({"topic": self.serializer_detail_class(topic, context={"request": request}).data},
                            status=status.HTTP_200_OK)
        return Response(DefaultErrorSerializer(dict(detail=TOPICS_ERRORS["id"])).data,
                        status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={
        status.HTTP_204_NO_CONTENT: None,
        status.HTTP_401_UNAUTHORIZED: DefaultErrorSerializer,
        status.HTTP_403_FORBIDDEN: DefaultErrorSerializer,
        status.HTTP_404_NOT_FOUND: DefaultErrorSerializer
    })
    def destroy(self, request, *args, **kwargs) -> Response:
        """ Удаление темы по ее id. """

        self.delete_topic(request, self.kwargs[self.lookup_url_kwarg])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(responses={
        status.HTTP_201_CREATED: None,
        status.HTTP_400_BAD_REQUEST: DefaultErrorSerializer,
        status.HTTP_401_UNAUTHORIZED: DefaultErrorSerializer,
    })
    def create(self, request, *args, **kwargs) -> Response:
        """ Создание новой темы на форуме. """

        flag = self.add_instance(request.user, request.data, request.data)
        data = DefaultErrorSerializer(dict(detail=flag.comment)).data if not flag.topic else dict()
        return Response(data, status=status.HTTP_201_CREATED if flag.topic else status.HTTP_400_BAD_REQUEST)


@extend_schema_view(get=extend_schema(responses={
    status.HTTP_200_OK: TopicsSerializer
}))
class GetSectionTopicsAPIView(ListAPIView):
    """ Получение топиков по конкретной секции форума. """

    serializer_class = TopicsSerializer
    lookup_url_kwarg = "section"

    def get_queryset(self):
        return Topic.objects.filter(section=self.kwargs[self.lookup_url_kwarg])


@extend_schema_view(get=extend_schema(responses={
    status.HTTP_200_OK: CommentSerializer,
    status.HTTP_404_NOT_FOUND: DefaultErrorSerializer
}))
class GetTopicCommentsAPIView(ListAPIView):
    """ Получение комментариев к конкретной теме форума. """

    serializer_class = CommentSerializer
    lookup_url_kwarg = "ids"

    def get_queryset(self):
        return get_object_or_404(Topic, pk=self.kwargs[self.lookup_url_kwarg]).comments


class AddCommentApiView(CreateAPIView, AddInstanceMixin):
    """ Добавление комментария к теме по ее id. """

    permission_classes = (IsAuthenticated,)
    serializer_class = validation_class = CommentSerializer
    request_host = RequestHost.APIVIEW

    @extend_schema(responses={
        status.HTTP_201_CREATED: None,
        status.HTTP_400_BAD_REQUEST: DefaultErrorSerializer,
        status.HTTP_401_UNAUTHORIZED: DefaultErrorSerializer
    })
    def post(self, request, *args, **kwargs) -> Response:
        flag = self.add_instance(request.user, request.data, request.data, request.data.get("topic", 0))
        data = DefaultErrorSerializer(dict(detail=flag.comment)).data if not flag.topic else dict()
        return Response(data, status=status.HTTP_201_CREATED if flag.topic else status.HTTP_400_BAD_REQUEST)


class GetUserAPIView(APIView):
    """ Получение информации о пользователе по его id. """

    serializer_class = UserSerializer

    @extend_schema(responses={
        status.HTTP_200_OK: serializer_class,
        status.HTTP_404_NOT_FOUND: DefaultErrorSerializer
    })
    def get(self, request: Request, ids: int) -> Response:
        user = get_object_or_404(User, pk=ids)
        context = {"request": request, "settings": UserSettings.objects.get(user=user)}
        data = self.serializer_class(user, context=context)
        return Response({"user": data.data}, status=status.HTTP_200_OK)


class UpdateSettingsApiView(APIView, UpdateSettingsMixin):
    """ Обновление настроек пользователя. """

    permission_classes = (IsAuthenticated,)
    request_host = RequestHost.APIVIEW

    @extend_schema(request=UpdateSettingsSerializer, responses={
        status.HTTP_201_CREATED: None,
        status.HTTP_204_NO_CONTENT: None,
        status.HTTP_400_BAD_REQUEST: DefaultErrorSerializer,
        status.HTTP_401_UNAUTHORIZED: DefaultErrorSerializer
    })
    def post(self, request: Request) -> Response:
        flag = self.update_settings(request.user, request.data, request.data)
        data = DefaultErrorSerializer(dict(detail=flag.flag_error)).data if flag.flag_error else dict()
        return (Response(data, status=status.HTTP_201_CREATED if flag.flag_success else
                (status.HTTP_400_BAD_REQUEST if flag.flag_error else status.HTTP_204_NO_CONTENT)))


class _ReviewOperation(APIView, AddReviewMixin, DropReviewMixin):
    class OnErrorReturn(NamedTuple):
        status: int
        message: str

    permission_classes = (IsAuthenticated,)
    like: Optional[bool] = None
    operation: str

    def post(self, request: Request, ids: int) -> Response:
        flag, user = getattr(self, self.operation)(request, {"pk": ids}, like=self.like)
        error_move = check_flag(self, user, flag)
        error = error_move if error_move else self.on_error(user, None)
        data = DefaultErrorSerializer(dict(detail=error.message)).data \
            if error.status == status.HTTP_400_BAD_REQUEST else dict()
        return Response(data, status=error.status)

    def on_error(self, user: User, error: Optional[int] = None) -> OnErrorReturn:
        data = (status.HTTP_400_BAD_REQUEST, get_rating_operation_error_message(error)) if error \
            else (status.HTTP_201_CREATED, "")
        return self.OnErrorReturn(*data)


@extend_schema_view(post=extend_schema(request=None, responses=review_operations_responses))
class LikeAPIView(_ReviewOperation):
    """ Позволяет лайкнуть пользователя по его id. """

    like = True
    operation = "add_review"


@extend_schema_view(post=extend_schema(request=None, responses=review_operations_responses))
class DislikeAPIView(_ReviewOperation):
    """ Позволяет дизлайкнуть пользователя по его id. """

    like = False
    operation = "add_review"


@extend_schema_view(post=extend_schema(request=None, responses=review_operations_responses))
class DropAPIView(_ReviewOperation):
    """ Позволяет сбросить оценку пользователя по его id. """

    operation = "drop_review"
