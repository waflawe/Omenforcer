from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.db.models import QuerySet

from forum_app.constants import Sections
from forum.settings import MEDIA_ROOT, MEDIA_URL, CUSTOM_TOPIC_UPLOADS_DIR, CUSTOM_COMMENT_UPLOADS_DIR
from services.common_utils import get_crop_upload_path

from typing import Literal
from os import remove


def _delete_upload(upload: ImageFieldFile | Literal[None]) -> Literal[None]:
    if upload:
        remove(get_crop_upload_path(upload.path))
        upload.delete(False)


def get_image_link(upload: ImageFieldFile | Literal[None]) -> str | Literal[None]:
    try:
        return MEDIA_URL + upload.path.split(MEDIA_ROOT)[-1]
    except ValueError:
        return ...


def process_topic_upload(instance: 'Topic', filename: str) -> str:
    return f"{CUSTOM_TOPIC_UPLOADS_DIR}/{instance.pk}.{filename.split('.')[-1]}"


def process_comment_upload(instance: 'Comment', filename: str) -> str:
    return f"{CUSTOM_COMMENT_UPLOADS_DIR}/{instance.pk}.{filename.split('.')[-1]}"


class Comment(models.Model):
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(validators=[MinLengthValidator(5)], max_length=2048)
    upload = models.ImageField(upload_to=process_comment_upload, null=True)
    time_added = models.DateTimeField(auto_now_add=True)

    def get_upload_link(self):
        return get_image_link(self.upload)

    class Meta:
        ordering = ("time_added",)


class Topic(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author")
    title = models.CharField(validators=[MinLengthValidator(8)], max_length=100)
    question = models.TextField(validators=[MinLengthValidator(5)], max_length=2048)
    upload = models.ImageField(upload_to=process_topic_upload, null=True)
    section = models.CharField(choices=Sections.Sections, max_length=10, default=Sections.GENERAL)
    views = models.PositiveIntegerField(default=0)
    time_added = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("forum_app:some_id", kwargs={"ids": self.pk, "section": self.section})

    def get_upload_link(self):
        return get_image_link(self.upload)

    @property
    def comments(self) -> QuerySet[Comment]:
        return (Comment.objects.select_related("author").only
                ("author__username", "author__id", "comment", "upload", "time_added").filter(topic=self))

    class Meta:
        ordering = ("-time_added",)

    def __str__(self):
        return f"{self.author} topic about '{self.title}'"


@receiver(pre_delete, sender=Topic)
def topic_upload_delete(sender, instance, **kwargs):
    _delete_upload(instance.upload)


@receiver(pre_delete, sender=Comment)
def topic_upload_delete(sender, instance, **kwargs):
    _delete_upload(instance.upload)
