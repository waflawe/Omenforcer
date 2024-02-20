from __future__ import annotations
from django.contrib.auth.models import User

from forum.settings import BASE_DIR, MEDIA_ROOT
from services.common_mixins import Error
from tasks.home_app_tasks import make_center_crop
from home_app.models import UserSettings
from home_app.forms import UploadAvatarForm

import os
from typing import Mapping, Literal, NamedTuple, Union
import pytz


class CheckAndSetSettingsReturn(NamedTuple):
    flag_error: Union[Literal[None], Literal["SUCCESS"], Error]
    flag_success: bool


class CheckOnEditionsReturn(NamedTuple):
    an_error_occured: bool
    error_code: Union[Literal[None], Literal["SUCCESS"], Error]


class SettingsMixin(object):
    class Fields:
        TIMEZONE_FIELD = "timezone"
        AVATAR_FIELD = "avatar"

    def check_and_set_settings(self, user: User, post: Mapping, files: Mapping) -> CheckAndSetSettingsReturn:
        flag_success = False

        for flag in (
                self._check_on_editions_select(user, post),
                self._check_on_editions_avatar(user, files)
        ):
            if flag.an_error_occured:
                return CheckAndSetSettingsReturn(flag.error_code, False)
            else:
                if flag.error_code:
                    flag_success = True

        return CheckAndSetSettingsReturn(False, flag_success)

    def _check_on_editions_select(self, user: User, data: Mapping) -> CheckOnEditionsReturn:
        user_settings = UserSettings.objects.get(user=user)
        timezone = data.get(self.Fields.TIMEZONE_FIELD, False)
        if timezone not in ("Default", False):
            try:
                tzone = timezone if not timezone.isnumeric() else pytz.common_timezones[int(timezone)]
            except IndexError:
                return CheckOnEditionsReturn(True, 3)
            flag = self._change_timezone(tzone, user_settings)
            if flag:
                return CheckOnEditionsReturn(True, flag)
            return CheckOnEditionsReturn(False, "SUCCESS")
        return CheckOnEditionsReturn(False, None)

    def _check_on_editions_avatar(self, user: User, data: Mapping) -> CheckOnEditionsReturn:
        if data.get(self.Fields.AVATAR_FIELD, False):
            flag = self._validate_and_save_avatar(user, data)
            if flag:
                return CheckOnEditionsReturn(True, flag)
            return CheckOnEditionsReturn(False, "SUCCESS")
        return CheckOnEditionsReturn(False, None)

    def _change_timezone(self, timezone: str, user_settings: UserSettings) -> Literal[None] | Error:
        if timezone not in pytz.common_timezones: return Error(3)
        user_settings.timezone = timezone
        user_settings.save()

    def _validate_and_save_avatar(self, user: User, data: Mapping) -> Literal[None] | Error:
        form = UploadAvatarForm(files=data, instance=UserSettings.objects.get(user=user))
        if form.is_valid():
            obj = self._save_photo_from_form(user, form)
            make_center_crop.delay(obj.avatar.path)
        else:
            return Error(1)

    def _save_photo_from_form(self, user: User, form: UploadAvatarForm) -> UserSettings:
        path_to_avatar_dir = f"{MEDIA_ROOT}avatars/{user.pk}/"
        try:
            for file in os.listdir(BASE_DIR / path_to_avatar_dir):
                os.remove(os.path.join(BASE_DIR, path_to_avatar_dir, file))
        except FileNotFoundError:
            pass
        return form.save()
