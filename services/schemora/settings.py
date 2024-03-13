from django.conf import settings
from django.utils.module_loading import import_string
from services.schemora.src.datastructures import Setting, Field, Error, Handler
from services.schemora.src.types import E, ErrorMessage

from typing import Type


class SchemoraSettings(object):
    """ Класс для получения настроек Schemor'ы. """

    def __init__(self):
        self.settings = getattr(settings, "SCHEMORA_SETTINGS")

    def __getitem__(self, item):
        try:
            return self.settings[item]
        except KeyError as e:
            raise AttributeError(f"Invalid Schemora setting: {item}") from e


schemora_settings = SchemoraSettings()


def get_user_settings_model() -> Type:
    """ Функция для ленивой загрузки модели настроек пользователя. """

    return import_string(schemora_settings["USER_SETTINGS_MODEL"])


def include_setting(*args, **kwargs) -> Setting:
    return Setting(
        Field(kwargs["field"]),
        Error(E(kwargs["error_code"]), ErrorMessage(kwargs.get("error_message", None))),
        Handler(kwargs["handler"], kwargs.get("validation_classes", None))
    )
