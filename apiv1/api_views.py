from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from forum_app.models import Topic
from apiv1.serializers import UserSerializer, TopicSerializer, CommentSerializer
from forum_app.constants import dict_sections
from apiv1.filters import TopicsSearchFilter
from services.forum_mixins import DeleteTopicMixin, AddInstanceMixin
from apiv1.permissions import TopicsOperationsPermission
from services.home_mixins import UpdateSettingsMixin, AddReviewMixin, DropReviewMixin
from services.home_app_utils import check_flag
from services.common_utils import RequestHost

from typing import Optional, NamedTuple


class GetSectionsAPIView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"sections": dict_sections})


class TopicViewSet(GenericViewSet, mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, DeleteTopicMixin, AddInstanceMixin):
    serializer_class = validation_class = TopicSerializer
    lookup_url_kwarg = "ids"
    filter_backends = (TopicsSearchFilter,)
    search_fields = ("title", "question", "author__username")
    permission_classes = (TopicsOperationsPermission,)

    def get_queryset(self):
        return Topic.objects.filter()

    def retrieve(self, request, *args, **kwargs) -> Response:
        try:
            topic = get_object_or_404(Topic, pk=self.kwargs[self.lookup_url_kwarg])
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response({"topic": self.serializer_class(topic, context={"request": request}).data})

    def destroy(self, request, *args, **kwargs) -> Response:
        self.delete_topic(request, self.kwargs[self.lookup_url_kwarg])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs) -> Response:
        topic, _ = self.add_instance(request.user, request.data, request.data)
        return Response(status=status.HTTP_201_CREATED if topic else status.HTTP_400_BAD_REQUEST)


class GetSectionTopicsAPIView(ListAPIView):
    serializer_class = TopicSerializer
    lookup_url_kwarg = "section"

    def get_queryset(self):
        return Topic.objects.filter(section=self.kwargs.get(self.lookup_url_kwarg, "general"))


class GetTopicCommentsAPIView(ListAPIView):
    serializer_class = CommentSerializer
    lookup_url_kwarg = "ids"

    def get_queryset(self):
        return get_object_or_404(Topic, pk=self.kwargs.get(self.lookup_url_kwarg, 0)).comments


class AddCommentApiView(CreateAPIView, AddInstanceMixin):
    permission_classes = (IsAuthenticated,)
    validation_class = CommentSerializer

    def post(self, request, *args, **kwargs) -> Response:
        try:
            _, comment = self.add_instance(request.user, request.data, request.data, request.data["topic"])
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED if comment else status.HTTP_400_BAD_REQUEST)


class GetUserAPIView(ListAPIView):
    serializer_class = UserSerializer
    pagination_class = None
    lookup_url_kwarg = "ids"

    def get_queryset(self):
        return User.objects.filter(pk=self.kwargs.get(self.lookup_url_kwarg, 0))


class UpdateSettingsApiView(APIView, UpdateSettingsMixin):
    permission_classes = (IsAuthenticated,)
    request_host = RequestHost.APIVIEW

    def post(self, request: Request) -> Response:
        flag = self.update_settings(request.user, request.data, request.data)
        return (Response(status=status.HTTP_201_CREATED if flag.flag_success else
                (status.HTTP_400_BAD_REQUEST if flag.flag_error else status.HTTP_204_NO_CONTENT)))


class _ReviewOperationTemplate(APIView, AddReviewMixin, DropReviewMixin):
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
        return Response({"message": error.message}, status=error.status)

    def on_error(self, user: User, error: Optional[int] = None) -> OnErrorReturn:
        data = (status.HTTP_400_BAD_REQUEST, "") if error else (status.HTTP_201_CREATED, "")
        return self.OnErrorReturn(*data)


class LikeAPIView(_ReviewOperationTemplate):
    like = True
    operation = "add_review"


class DislikeAPIView(_ReviewOperationTemplate):
    like = False
    operation = "add_review"


class DropAPIView(_ReviewOperationTemplate):
    operation = "drop_review"
