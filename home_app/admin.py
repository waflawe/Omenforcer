from django.contrib import admin

from services.schemora.settings import get_user_settings_model

UserSettings = get_user_settings_model()


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = "pk", "user", "timezone", "avatar"
    list_display_links = "pk", "user"
    search_fields = "pk", "user"
