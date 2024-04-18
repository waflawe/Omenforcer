from os import remove
from typing import Literal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import QuerySet
from django.db.models.fields.files import ImageFieldFile
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.urls import reverse

from forum_app.constants import Sections
from schemora.settings.helpers import get_upload_crop_path


def _delete_upload(upload: ImageFieldFile | Literal[None]) -> Literal[None]:
    if upload:
        remove(get_upload_crop_path(upload.path))
        upload.delete(False)


def get_image_link(upload: ImageFieldFile | Literal[None]) -> str | Literal[None]:
    try:
        return settings.MEDIA_URL + upload.path.split(settings.MEDIA_ROOT)[-1]
    except ValueError:
        return None


def process_topic_upload(instance: 'Topic', filename: str) -> str:
    return f"{settings.CUSTOM_TOPIC_UPLOADS_DIR}/{instance.pk}.{filename.split('.')[-1]}"


def process_comment_upload(instance: 'Comment', filename: str) -> str:
    return f"{settings.CUSTOM_COMMENT_UPLOADS_DIR}/{instance.pk}.{filename.split('.')[-1]}"


class Comment(models.Model):
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(validators=[MinLengthValidator(5)], max_length=2048)
    upload = models.ImageField(upload_to=process_comment_upload, null=True)
    time_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("time_added",)

    def __str__(self):
        return f"{self.topic} comment by {self.author}."

    def get_upload_link(self):
        return get_image_link(self.upload)


class Topic(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author")
    title = models.CharField(validators=[MinLengthValidator(8)], max_length=100)
    question = models.TextField(validators=[MinLengthValidator(5)], max_length=2048)
    upload = models.ImageField(upload_to=process_topic_upload, null=True)
    section = models.CharField(choices=Sections.Sections, max_length=10, default=Sections.GENERAL)
    views = models.PositiveIntegerField(default=0)
    time_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-time_added",)

    def __str__(self):
        return f"{self.author} topic about '{self.title}'"

    def get_absolute_url(self):
        return reverse("forum_app:some_id", kwargs={"ids": self.pk, "section": self.section})

    def get_upload_link(self):
        return get_image_link(self.upload)

    @property
    def comments(self) -> QuerySet[Comment]:
        return (Comment.objects.select_related("author").only
                ("author__username", "author__id", "comment", "upload", "time_added").filter(topic=self))


@receiver(pre_delete, sender=Topic)
def topic_upload_delete(sender, instance, **kwargs):
    _delete_upload(instance.upload)


@receiver(pre_delete, sender=Comment)
def comment_upload_delete(sender, instance, **kwargs):
    _delete_upload(instance.upload)
