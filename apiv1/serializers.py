from __future__ import annotations

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth.models import User

from forum_app.models import Topic, Comment, get_image_link
from home_app.models import Review, UserRating
from schemora.settings.helpers import get_user_settings_model, get_instance_datetime_attribute, get_user_settings
from services.user_settings import settings

UserSettings = get_user_settings_model()


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
        return get_instance_datetime_attribute(self.context["request"].user, topic)

    @extend_schema_field(OpenApiTypes.STR)
    def get_author_signature(self, comment):
        return get_user_settings(comment.author).signature


class TopicsSerializer(_InstanceSerializer):
    class Meta:
        model = Topic
        fields = "id", "title", "views", "author", "section", "time_added"
        read_only_fields = "id", "views", "author", "time_added"


class TopicDetailSerializer(_InstanceSerializer):
    class Meta:
        model = Topic
        fields = (
            "id", "title", "question", "upload", "views", "author", "author_signature",
            "section", "time_added"
        )
        read_only_fields = "id", "views", "author", "author_signature", "time_added"


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
        return get_instance_datetime_attribute(self.context["request"].user, user, attribute="date_joined")

    @extend_schema_field(serializers.DictField)
    def get_last_login(self, user):
        return get_instance_datetime_attribute(self.context["request"].user, user, attribute="last_login")

    @extend_schema_field(OpenApiTypes.INT)
    def get_rating(self, user):
        return UserRating.objects.get(user=user).rating

    @extend_schema_field(OpenApiTypes.INT)
    def get_reviews_count(self, user):
        return Review.objects.filter(user=user).count()

    @extend_schema_field(OpenApiTypes.STR)
    def get_signature(self, user):
        return self.context["settings"].signature
