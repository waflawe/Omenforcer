from django.contrib.auth.models import User
from django.db import models

from forum.settings import DEFAULT_USER_AVATAR_FILENAME, CUSTOM_USER_AVATARS_DIR
from services.user_settings_core import EMPTY_FIELD_VALUE


def process_upload_user_avatar(instance: 'UserSettings', filename: str) -> str:
    return f"{CUSTOM_USER_AVATARS_DIR}/{instance.user.pk}/{instance.user.pk}.{filename.split('.')[-1]}"


class UserSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=50, default=EMPTY_FIELD_VALUE)
    avatar = models.ImageField(upload_to=process_upload_user_avatar, default=DEFAULT_USER_AVATAR_FILENAME)


class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reviewer")
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    feedback = models.BooleanField(null=True)
    time_added = models.DateTimeField(auto_now=True)


class UserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    rating = models.IntegerField(default=0)
