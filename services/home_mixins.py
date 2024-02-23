from __future__ import annotations
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from home_app.models import UserSettings
from services.user_settings import settings
from services.user_settings_core import Setting, E

from typing import Dict, Literal, NamedTuple, Union


class CheckAndSetSettingsReturn(NamedTuple):
    flag_error: Union[Literal[None], Literal["SUCCESS"], E]
    flag_success: bool


class CheckOnEditionsReturn(NamedTuple):
    an_error_occured: bool
    error_code: Union[Literal[None], Literal["SUCCESS"], E]


class UpdateSettingsMixin(object):
    """ Миксин для обновления настроек пользователя, прописанных в файле services.user_settings. """

    request_host = None   # переменная-источник запроса. Имеет значение RequestHost.APIVIEW или RequestHost.VIEW

    def update_settings(self, user: User, post: Dict, files: Dict) -> CheckAndSetSettingsReturn:
        flag_success = False
        user_settings, data = get_object_or_404(UserSettings, user=user), post | files

        for setting in settings:
            flag = self._process_setting(setting, user_settings, post, files)
            if flag.an_error_occured:
                return CheckAndSetSettingsReturn(flag.error_code, False)
            else:
                if flag.error_code:
                    flag_success = True

        return CheckAndSetSettingsReturn(False, flag_success)

    def _process_setting(self, setting: Setting, user_settings: UserSettings, post: Dict, files: Dict) \
            -> CheckOnEditionsReturn:
        if any((post.get(setting.field.field, False), files.get(setting.field.field, False))):
            if setting.handler.handler().handle(setting, user_settings, post=post, files=files,
                                                request_host=self.request_host):
                return CheckOnEditionsReturn(True, setting.error.error_code)
            return CheckOnEditionsReturn(False, "SUCCESS")
        return CheckOnEditionsReturn(False, None)
