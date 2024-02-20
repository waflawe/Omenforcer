from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from services.apiv1_utils import *
from forum_app.models import *
from .serializers import UserSerializer, TopicSerializer, TopicDetailSerializer, CommentSerializer
from forum_app.constants import dict_sections
from .filters import TopicSearchFilter
from apiv1.mixins import AddInstanceAPIMixin


class GetUserAPIView(ListAPIView):
    serializer_class = UserSerializer
    pagination_class = None

    def get_queryset(self):
        return User.objects.filter(pk=self.kwargs["ids"])


class GetTopicsAPIView(ListAPIView):
    serializer_class = TopicSerializer
    filter_backends = (TopicSearchFilter,)
    search_fields = ("title", "question", "author__username")

    def get_queryset(self):
        queryset = Topic.objects.all()
        queryset = queryset.filter(section=self.kwargs["section"]) if self.kwargs.get("section", False) else queryset
        return queryset.order_by('time_added')


class GetTopicDetailAPIView(ListAPIView):
    serializer_class = TopicDetailSerializer
    pagination_class = None

    def get_queryset(self):
        return Topic.objects.filter(pk=self.kwargs["ids"])


class GetTopicCommentsAPIView(ListAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = Comments.objects.all()
        return queryset.filter(topic=get_object_or_404(Topic, pk=self.kwargs["ids"])).all()


class AddTopicApiView(APIView, AddInstanceAPIMixin):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        return Response(self.add_instance(request))


class AddCommentApiView(APIView, AddInstanceAPIMixin):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        return Response(self.add_instance(request, is_instance_topic=False))


class DeleteTopicApiView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, ids: int) -> Response:
        return Response(DeleteTopicApiViewUtils().delete_topic_api_view(request, ids))


class UpdateSettingsApiView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        return Response(UpdateSettingsApiViewUtils().update_settings_api_view(request))


class GetSectionsAPIView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"sections": dict_sections})
