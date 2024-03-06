from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from forum_app.models import Topic
from apiv1.serializers import UserSerializer, TopicSerializer, CommentSerializer
from forum_app.constants import dict_sections
from apiv1.filters import TopicsSearchFilter
from services.forum_mixins import DeleteTopicMixin, AddInstanceMixin, get_topic_and_validate_section
from services.home_mixins import (UpdateSettingsMixin, AddReviewMixin, DropReviewMixin,
                                  get_rating_operation_error_message)
from services.home_app_utils import check_flag
from services.common_utils import RequestHost
from home_app.models import UserSettings
from error_messages.forum_error_messages import TOPICS_ERRORS

from typing import Optional, NamedTuple


class GetSectionsAPIView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"sections": dict_sections})


class TopicViewSet(GenericViewSet, mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, DeleteTopicMixin, AddInstanceMixin):
    """ Вьюсет для отображения всех, отображения одной, удаления, создания тем на форуме. """

    serializer_class = validation_class = TopicSerializer
    queryset = Topic.objects.all()
    lookup_url_kwarg = "ids"
    filter_backends = (TopicsSearchFilter,)
    search_fields = ("title", "question", "author__username")
    permission_classes = (IsAuthenticatedOrReadOnly,)
    request_host = RequestHost.APIVIEW

    def retrieve(self, request, *args, **kwargs) -> Response:
        try:
            topic, _ = get_topic_and_validate_section(int(self.kwargs[self.lookup_url_kwarg]))
        except ValueError:
            return Response({"error_message": TOPICS_ERRORS["id"]}, status=status.HTTP_400_BAD_REQUEST)
        context = {"request": request, "view_detail_info": True}
        return Response({"topic": self.serializer_class(topic, context=context).data})

    def destroy(self, request, *args, **kwargs) -> Response:
        flag = self.delete_topic(request, self.kwargs[self.lookup_url_kwarg])
        data = dict(error_message=flag.message) if not flag.status else dict()
        return Response(data, status=status.HTTP_204_NO_CONTENT if flag.status else status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs) -> Response:
        flag = self.add_instance(request.user, request.data, request.data, serializer_context={"view_detail_info": True})
        data = dict(error_message=flag.comment) if not flag.topic else dict()
        return Response(data, status=status.HTTP_201_CREATED if flag.topic else status.HTTP_400_BAD_REQUEST)


class GetSectionTopicsAPIView(ListAPIView):
    serializer_class = TopicSerializer
    lookup_url_kwarg = "section"

    def get_queryset(self):
        return Topic.objects.filter(section=self.kwargs[self.lookup_url_kwarg])


class GetTopicCommentsAPIView(ListAPIView):
    serializer_class = CommentSerializer
    lookup_url_kwarg = "ids"

    def get_queryset(self):
        return get_object_or_404(Topic, pk=self.kwargs[self.lookup_url_kwarg]).comments


class AddCommentApiView(CreateAPIView, AddInstanceMixin):
    permission_classes = (IsAuthenticated,)
    validation_class = CommentSerializer

    def post(self, request, *args, **kwargs) -> Response:
        flag = self.add_instance(request.user, request.data, request.data, request.data.get("topic", 0))
        data = dict(error_message=flag.topic) if not flag.comment else dict()
        return Response(data, status=status.HTTP_201_CREATED if flag.comment else status.HTTP_400_BAD_REQUEST)


class GetUserAPIView(APIView):
    serializer_class = UserSerializer

    def get(self, request: Request, ids: int) -> Response:
        user = get_object_or_404(User, pk=ids)
        context = {"request": request, "settings": UserSettings.objects.get(user=user)}
        data = self.serializer_class(user, context=context)
        return Response({"user": data.data})


class UpdateSettingsApiView(APIView, UpdateSettingsMixin):
    permission_classes = (IsAuthenticated,)
    request_host = RequestHost.APIVIEW

    def post(self, request: Request) -> Response:
        flag = self.update_settings(request.user, request.data, request.data)
        data = dict(error_message=flag.flag_error) if flag.flag_error else dict()
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
        flag, user = getattr(self, self.operation)(request, ids, like=self.like)
        error_move = check_flag(self, user, flag)
        error = error_move if error_move else self.on_error(user, None)
        data = dict(error_message=error.message) if error.status == status.HTTP_400_BAD_REQUEST else dict()
        return Response(data, status=error.status)

    def on_error(self, user: User, error: Optional[int] = None) -> OnErrorReturn:
        data = (status.HTTP_400_BAD_REQUEST, get_rating_operation_error_message(error)) if error \
            else (status.HTTP_201_CREATED, "")
        return self.OnErrorReturn(*data)


class LikeAPIView(_ReviewOperation):
    like = True
    operation = "add_review"


class DislikeAPIView(_ReviewOperation):
    like = False
    operation = "add_review"


class DropAPIView(_ReviewOperation):
    operation = "drop_review"
