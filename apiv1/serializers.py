from __future__ import annotations
from rest_framework import serializers
from rest_framework.request import Request

from forum_app.models import *
from home_app.models import UserSettings

import pytz
from datetime import datetime
from typing import Tuple


def set_datetime_to_timezone(dt: datetime, timezone: str) -> Tuple[datetime, str]:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return (dt + dt.utcoffset()), timezone


def get_instance_time_attribute(request: Request, instance: 'Topic' | 'Comments', attribute: str = "time_added"):
    dt, timezone = getattr(instance, attribute), "UTC"
    user_timezone = UserSettings.objects.get(user=request.user).timezone if request.user.is_authenticated else "Default"
    if request.user.is_authenticated and user_timezone != "Default":
        dt, timezone = set_datetime_to_timezone(dt, user_timezone)
    return {
        attribute: dt.strftime("%H:%M %d/%m/%Y"),
        "time_zone": timezone,
    }


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "id", "title", "views", "author", "section"


class TopicDetailSerializer(serializers.ModelSerializer):
    upload = serializers.CharField(source="get_upload_info")
    time_added = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = "id", "title", "question", "views", "author", "section", "upload", "time_added"

    def get_time_added(self, topic):
        return get_instance_time_attribute(self.context["request"], topic)


class CommentSerializer(serializers.ModelSerializer):
    upload = serializers.CharField(source="get_upload_info")
    time_added = serializers.SerializerMethodField()

    class Meta:
        model = Comments
        fields = "id", "topic", "comment", "author", "upload", "time_added"

    def get_time_added(self, comment):
        return get_instance_time_attribute(self.context["request"], comment)


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    date_joined = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "id", "username", "avatar", "date_joined", "last_login"

    def get_avatar(self, user):
        return get_image_link(UserSettings.objects.get(user=user).avatar)

    def get_date_joined(self, user):
        return get_instance_time_attribute(self.context["request"], user, attribute="date_joined")

    def get_last_login(self, user):
        return get_instance_time_attribute(self.context["request"], user, attribute="last_login")
