from __future__ import annotations
from rest_framework import serializers
from rest_framework.request import Request

from forum_app.models import *
from home_app.models import UserSettings, Review, UserRating
from services.user_settings_core import EMPTY_FIELD_VALUE

import pytz
from datetime import datetime
from typing import Tuple


def set_datetime_to_timezone(dt: datetime, timezone: str) -> Tuple[datetime, str]:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return (dt + dt.utcoffset()), timezone


def get_instance_time_attribute(request: Request, instance: 'Topic' | 'Comments', attribute: str = "time_added"):
    dt, timezone = getattr(instance, attribute), "UTC"
    user_timezone = UserSettings.objects.get(user=request.user).timezone if request.user.is_authenticated else (
        EMPTY_FIELD_VALUE
    )
    if request.user.is_authenticated and user_timezone != EMPTY_FIELD_VALUE:
        dt, timezone = set_datetime_to_timezone(dt, user_timezone)
    return {
        attribute: dt.strftime("%H:%M %d/%m/%Y"),
        "time_zone": timezone,
    }


class CustomImageField(serializers.ImageField):
    def to_representation(self, value):
        return get_image_link(value)


class TopicSerializer(serializers.ModelSerializer):
    upload = CustomImageField(required=False)
    time_added = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Topic
        fields = "id", "title", "question", "views", "author", "section", "upload", "time_added"
        read_only_fields = "author", "id", "time_added", "views"

    def get_time_added(self, topic):
        return get_instance_time_attribute(self.context["request"], topic)


class CommentSerializer(serializers.ModelSerializer):
    upload = CustomImageField(required=False)
    time_added = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comments
        fields = "id", "topic", "comment", "author", "upload", "time_added"
        read_only_fields = "id", "author", "time_added"

    def get_time_added(self, comment):
        return get_instance_time_attribute(self.context["request"], comment)


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField(read_only=True)
    date_joined = serializers.SerializerMethodField(read_only=True)
    last_login = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField(read_only=True)
    reviews_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = "id", "username", "avatar", "date_joined", "last_login", "rating", "reviews_count"

    def get_avatar(self, user):
        return get_image_link(UserSettings.objects.get(user=user).avatar)

    def get_date_joined(self, user):
        return get_instance_time_attribute(self.context["request"], user, attribute="date_joined")

    def get_last_login(self, user):
        return get_instance_time_attribute(self.context["request"], user, attribute="last_login")

    def get_rating(self, user):
        return UserRating.objects.get(user=user).rating

    def get_reviews_count(self, user):
        return Review.objects.filter(user=user).count()


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ("avatar",)
