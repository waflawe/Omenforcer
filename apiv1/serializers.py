from __future__ import annotations

from rest_framework import serializers
from rest_framework.request import Request

from forum_app.models import *
from home_app.models import UserSettings, Review, UserRating
from forum.settings import DEFAULT_USER_TIMEZONE

import pytz
from datetime import datetime
from typing import Tuple


def get_datetime_in_timezone(dt: datetime, timezone: str) -> Tuple[datetime, str]:
    """ Получение datetime объекта в определенной временной зоне."""

    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return (dt + dt.utcoffset()), timezone


def get_instance_time_attribute(request: Request, instance: 'Topic' | 'Comments', attribute: str = "time_added"):
    """ Получение временного атрибута темы или комментария. """

    dt, timezone = getattr(instance, attribute), "UTC"
    user_timezone = UserSettings.objects.get(user=request.user).timezone if request.user.is_authenticated else (
        DEFAULT_USER_TIMEZONE
    )
    if request.user.is_authenticated and user_timezone != DEFAULT_USER_TIMEZONE:
        dt, timezone = get_datetime_in_timezone(dt, user_timezone)
    return {
        attribute: dt.strftime("%H:%M %d/%m/%Y"),
        "time_zone": timezone,
    }


class CustomImageField(serializers.ImageField):
    def to_representation(self, value):
        return get_image_link(value)


class _InstanceSerializer(serializers.ModelSerializer):
    upload = CustomImageField(required=False)
    time_added = serializers.SerializerMethodField(read_only=True)
    author_signature = serializers.SerializerMethodField(read_only=True)

    def get_time_added(self, topic):
        return get_instance_time_attribute(self.context["request"], topic)

    def get_author_signature(self, comment):
        return UserSettings.objects.get(user=comment.author).signature


class TopicSerializer(_InstanceSerializer):
    detail_fields = ("question", "upload", "author_signature")

    class Meta:
        model = Topic
        fields = ["id", "title", "views", "author", "section", "time_added"]
        read_only_fields = ["author", "id", "time_added", "views"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("view_detail_info", False): self.update_serializer_fields("append")
        else: self.update_serializer_fields("remove")

    def update_serializer_fields(self, method_to_update: Literal["append"] | Literal["remove"]):
        try:
            for detail_field in self.detail_fields:
                getattr(self.Meta.fields, method_to_update)(detail_field)
            getattr(self.Meta.read_only_fields, method_to_update)("author_signature")
        except ValueError:
            pass


class CommentSerializer(_InstanceSerializer):
    class Meta:
        model = Comments
        fields = "id", "topic", "comment", "author", "upload", "time_added", "author_signature"
        read_only_fields = "id", "author", "time_added", "author_signature"


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField(read_only=True)
    date_joined = serializers.SerializerMethodField(read_only=True)
    last_login = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField(read_only=True)
    reviews_count = serializers.SerializerMethodField(read_only=True)
    signature = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = "id", "username", "avatar", "date_joined", "last_login", "rating", "reviews_count", "signature"

    def get_avatar(self, user):
        return get_image_link(self.context["settings"].avatar)

    def get_date_joined(self, user):
        return get_instance_time_attribute(self.context["request"], user, attribute="date_joined")

    def get_last_login(self, user):
        return get_instance_time_attribute(self.context["request"], user, attribute="last_login")

    def get_rating(self, user):
        return UserRating.objects.get(user=user).rating

    def get_reviews_count(self, user):
        return Review.objects.filter(user=user).count()

    def get_signature(self, user):
        return self.context["settings"].signature


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ("avatar",)


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ("signature",)
