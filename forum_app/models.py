from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from .constants import Sections
from forum.settings import MEDIA_ROOT, MEDIA_URL
from services.common_mixins import get_crop_upload_path

from typing import Literal
from os import remove


def _delete_upload(upload: ImageFieldFile) -> Literal[None]:
    remove(get_crop_upload_path(upload.path))
    upload.delete(False)


def get_image_link(upload: ImageFieldFile | Literal[None]) -> str | Literal[None]:
    try:
        return MEDIA_URL + upload.path.split(MEDIA_ROOT)[-1]
    except ValueError:
        return


def process_topic_upload(instance: 'Topic', filename: str) -> str:
    return f"t_images/{instance.pk}.{filename.split('.')[-1]}"


def process_comment_upload(instance: 'Comments', filename: str) -> str:
    return f"c_images/{instance.pk}.{filename.split('.')[-1]}"


class Topic(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author")
    title = models.CharField(validators=[MinLengthValidator(8)], max_length=100, null=True, unique=True)
    question = models.TextField(validators=[MinLengthValidator(5)], max_length=2048, null=True, unique=True)
    upload = models.ImageField(upload_to=process_topic_upload, null=True)
    section = models.CharField(choices=Sections.Sections, max_length=10, default=Sections.GENERAL)
    views = models.PositiveIntegerField(default=0)
    time_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}."

    def get_absolute_url(self):
        return reverse("forum_app:some_id", kwargs={"ids": self.pk, "section": self.section})

    def get_upload_info(self):
        return get_image_link(self.upload)


class Comments(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(validators=[MinLengthValidator(5)], max_length=2048, null=True)
    upload = models.ImageField(upload_to=process_comment_upload, null=True)
    time_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment for {self.topic} from {self.author}."

    def get_upload_info(self):
        return get_image_link(self.upload)


@receiver(pre_delete, sender=Topic)
def topic_upload_delete(sender, instance, **kwargs):
    if instance.upload:
        _delete_upload(instance.upload)


@receiver(pre_delete, sender=Comments)
def topic_upload_delete(sender, instance, **kwargs):
    if instance.upload:
        _delete_upload(instance.upload)
