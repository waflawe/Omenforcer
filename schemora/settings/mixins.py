from importlib import import_module
from typing import Dict, Optional

from schemora.conf import schemora_settings
from schemora.core.datastructures import Setting
from schemora.core.enums import RequestHost
from schemora.core.mixins import DataValidationMixin
from schemora.core.types import E, ValidationClass
from schemora.settings.helpers import get_user_settings_model

UserSettings = get_user_settings_model()


class BaseDataValidationHandlerMixin(DataValidationMixin):
    """
    Базовый миксин для создания обработчика настройки с использованием
    класса schemora.core.mixins.DataValidationMixin.
    """

    class ReceivedData:
        data: Optional[Dict] = None
        files: Optional[Dict] = None

    def __init__(self):
        self.received_data = self.ReceivedData()

    def data_validation_update_setting(self, setting: Setting, user_settings: UserSettings,
                                       request_host: RequestHost) -> UserSettings | E:
        data, files = ((getattr(self.received_data, attr) if getattr(self.received_data, attr) else dict())
                       for attr in ("data", "files"))
        self.validation_class = self.get_validation_class(setting, request_host)
        v, is_valid, data = self.validate_received_data(data, files, instance=user_settings)
        if is_valid:
            return v.save()
        else:
            return setting.error.error_code

    def get_validation_class(self, setting: Setting, request_host: RequestHost) -> ValidationClass:
        """ Функция для ленивой загрузки класса-валидатора. """

        validation_classes = setting.handler.validation_classes
        validation_class = (validation_classes.web_validation_class if request_host == RequestHost.VIEW
                            else validation_classes.api_validation_class)
        smodule = schemora_settings.USER_SETTINGS.SERIALIZERS_MODULE
        fmodule = schemora_settings.USER_SETTINGS.FORMS_MODULE
        return getattr(import_module(smodule if request_host == RequestHost.APIVIEW else fmodule), validation_class)
