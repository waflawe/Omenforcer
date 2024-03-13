from __future__ import annotations

from rest_framework import serializers
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth.models import User

from forum_app.models import Topic, Comment, get_image_link
from home_app.models import Review, UserRating
from forum.settings import DEFAULT_USER_TIMEZONE
from services.schemora.settings import get_user_settings_model
from services.user_settings import settings

import pytz
from datetime import datetime
from typing import Tuple, Any

UserSettings = get_user_settings_model()


def get_datetime_in_timezone(dt: datetime, timezone: str) -> Tuple[datetime, str]:
    """ Получение datetime объекта в определенной временной зоне. """

    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return (dt + dt.utcoffset()), timezone


def get_instance_time_attribute(request: Request, instance: Any, attribute: str = "time_added"):
    """ Получение DateTime атрибута объекта в выбранной временной зоне текущего пользователя. """

    try:
        dt, timezone = getattr(instance, attribute), "UTC"
    except AttributeError as e:
        raise RuntimeError(f"Invalid {instance.__class__.__name__} attribute: {attribute}") from e
    user_timezone = UserSettings.objects.get(user=request.user).timezone if request.user.is_authenticated else (
        DEFAULT_USER_TIMEZONE
    )
    if request.user.is_authenticated and user_timezone != DEFAULT_USER_TIMEZONE:
        dt, timezone = get_datetime_in_timezone(dt, user_timezone)
    return {
        attribute: dt.strftime("%H:%M %d/%m/%Y"),
        "time_zone": timezone,
    }


class SectionsSerializer(serializers.Serializer):
    sections = serializers.DictField()


class DefaultErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class UpdateSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = tuple(setting.field.field for setting in settings)
        optional_fields = tuple(setting.field.field for setting in settings)


@extend_schema_field(OpenApiTypes.STR)
class CustomImageField(serializers.ImageField):
    def to_representation(self, value):
        return get_image_link(value)


class _InstanceSerializer(serializers.ModelSerializer):
    upload = CustomImageField(required=False)
    time_added = serializers.SerializerMethodField(read_only=True)
    author_signature = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(serializers.DictField)
    def get_time_added(self, topic):
        return get_instance_time_attribute(self.context["request"], topic)

    @extend_schema_field(OpenApiTypes.STR)
    def get_author_signature(self, comment):
        return UserSettings.objects.get(user=comment.author).signature


class _TopicBaseSerializer(_InstanceSerializer):
    comments_count = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.INT)
    def get_comments_count(self, topic):
        return topic.comments.count()


class TopicsSerializer(_TopicBaseSerializer):
    class Meta:
        model = Topic
        fields = "id", "title", "views", "comments_count", "author", "section", "time_added"
        read_only_fields = "id", "views", "comments_count", "author", "time_added"


class TopicDetailSerializer(_TopicBaseSerializer):
    class Meta:
        model = Topic
        fields = ("id", "title", "question", "upload", "views", "comments_count", "author", "author_signature",
                  "section", "time_added")
        read_only_fields = "id", "views", "comments_count", "author", "author_signature", "time_added"


class CommentSerializer(_InstanceSerializer):
    class Meta:
        model = Comment
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

    @extend_schema_field(OpenApiTypes.STR)
    def get_avatar(self, user):
        return get_image_link(self.context["settings"].avatar)

    @extend_schema_field(serializers.DictField)
    def get_date_joined(self, user):
        return get_instance_time_attribute(self.context["request"], user, attribute="date_joined")

    @extend_schema_field(serializers.DictField)
    def get_last_login(self, user):
        return get_instance_time_attribute(self.context["request"], user, attribute="last_login")

    @extend_schema_field(OpenApiTypes.INT)
    def get_rating(self, user):
        return UserRating.objects.get(user=user).rating

    @extend_schema_field(OpenApiTypes.INT)
    def get_reviews_count(self, user):
        return Review.objects.filter(user=user).count()

    @extend_schema_field(OpenApiTypes.STR)
    def get_signature(self, user):
        return self.context["settings"].signature


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = "avatar",


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = "signature",
