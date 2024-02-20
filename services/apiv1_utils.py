from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.request import Request

from forum_app.models import Topic
from apiv1.serializers import TopicSerializer
from services.common_mixins import *
from services.home_mixins import SettingsMixin
from services.forum_mixins import DeleteTopicMixin

from typing import Dict


def get_topic_detail_api_view(request: Request, ids: int) -> Dict:
    return dict(TopicSerializer(get_object_or_404(Topic, pk=ids)).data)


class DeleteTopicApiViewUtils(DeleteTopicMixin):
    def delete_topic_api_view(self, request: Request, ids: int) -> Dict:
        topic = get_object_or_404(Topic, pk=ids)
        if topic.author == request.user or request.user.is_superuser():
            self.delete_topic(topic)
            return {"success": "True"}
        return {"success": "False", "message": "Вы не имеете прав."}


class UpdateSettingsApiViewUtils(SettingsMixin):
    def update_settings_api_view(self, request: Request) -> Dict:
        flag_error, flag_success = self.check_and_set_settings(request.user, request.POST, request.FILES)
        if flag_success:
            return {"success": "True"}
        elif flag_error:
            return {"success": "False", "message": f"{flag_error}"}
        return dict()
