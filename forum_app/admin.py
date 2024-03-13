from django.contrib import admin

from forum_app import models


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = "pk", "title", "question_short", "views", "time_added"
    list_display_links = "pk", "title"
    ordering = "-pk",
    search_fields = "pk", "title"

    def question_short(self, obj: models.Topic) -> str:
        return obj.question if len(obj.question) < 56 else obj.question[:56] + "..."


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = "pk", "comment_short", "time_added"
    list_display_links = "pk",
    search_fields = "pk", "comment"

    def comment_short(self, obj: models.Comment) -> str:
        return obj.comment if len(obj.comment) < 56 else obj.comment[:56] + "..."
