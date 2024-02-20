from django.contrib.auth.models import User
from django.db import models


def process_upload_user_avatar(instance: 'UserSettings', filename: str) -> str:
    return f"avatars/{instance.user.pk}/{instance.user.pk}.{filename.split('.')[-1]}"


class UserSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=50, default="Default")
    avatar = models.ImageField(upload_to=process_upload_user_avatar, default="default-user-icon.jpg")
