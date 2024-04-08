from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

from schemora.conf import schemora_settings


def process_upload_user_avatar(instance: 'UserSettings', filename: str) -> str:
    return f"{settings.CUSTOM_USER_AVATARS_DIR}/{instance.user.pk}/{instance.user.pk}.{filename.split('.')[-1]}"


class UserSettings(models.Model):
    """ Модель настроек пользователя. """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=30, default=schemora_settings.USER_SETTINGS.DEFAULT_USER_TIMEZONE)
    avatar = models.ImageField(upload_to=process_upload_user_avatar,
                               default=schemora_settings.USER_SETTINGS.DEFAULT_USER_AVATAR_FILENAME)
    signature = models.CharField(max_length=64, null=True)


class Review(models.Model):
    """ Модель отзывов на пользователей. """

    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviewer")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.BooleanField(null=True)
    time_added = models.DateTimeField(auto_now=True)


class UserRating(models.Model):
    """ Модель рейтинга конкретного камрада. """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
