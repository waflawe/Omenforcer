from django.contrib import admin

from . import models


@admin.register(models.UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "timezone", "avatar"]
    list_display_links = ["pk", "user"]
    search_fields = ["pk", "user"]
