from django.conf import settings as djsettings

from typing import Any, Mapping, Optional

settings = getattr(djsettings, "SCHEMORA_SETTINGS")


class Empty:
    pass


class DefaultSupportingSettingWrapper:
    def __init__(self, defaults: Optional[Mapping | Any] = None):
        self.defaults = defaults


class RequiredSetting:
    pass


class OptionalSetting(DefaultSupportingSettingWrapper):
    pass


class DependentSetting(DefaultSupportingSettingWrapper):
    def __init__(self, depended: str, *args, **kwargs):
        self.depended = depended
        super().__init__(*args, **kwargs)


DEFAULTS = {
    "USER_SETTINGS": {
        "USER_SETTINGS_MODEL": RequiredSetting(),
        "SERIALIZERS_MODULE": RequiredSetting(),
        "FORMS_MODULE": RequiredSetting(),
        "DEFAULT_USER_AVATAR_FILENAME": OptionalSetting(None),
        "DEFAULT_USER_TIMEZONE": OptionalSetting("UTC"),
    },
    "CACHE": {
        "USER_SETTINGS_CACHE_NAME": DependentSetting("USER_SETTINGS", "user_settings"),
        "USER_SETTINGS_CACHE_TIMEOUT": DependentSetting("USER_SETTINGS", 60),
        "USER_DEFINED_CACHE_NAME_DELIMITER": OptionalSetting(":")
    },
}


class _NestedSetting:
    """ Класс вложенной (second-level) настройки. """

    def __init__(self, value: Mapping, parent: str, settings_: Mapping):
        self.settings = settings_
        self.value = value
        self.parent = parent

    def __get_second_level_setting(self, item):
        default = DEFAULTS.get(self.parent,).get(item, None)
        assert default, AssertionError(f"Invalid Schemora setting: {self.parent}.{item}")
        if isinstance(default, DependentSetting):
            assert default.depended in self.settings.keys(), AssertionError(
                f"{self.parent}.{item} is a DependentSetting, but his guardian is not defined."
            )
        if item not in self.value.keys():
            assert isinstance(default, OptionalSetting), AssertionError(
                f"{self.parent}.{item} Schemora setting is not defined."
            )
            return default.defaults
        return self.value[item]

    def __getitem__(self, item):
        return self.__get_second_level_setting(item)

    def __getattr__(self, item):
        return self.__get_second_level_setting(item)


class SchemoraSettings:
    """
    Класс для получения настроек Schemor'ы.

    Валидаторы настроек предполагают, что:
    1. Все не вложенные настройки на глобальном уровне являются RequiredSetting's.
    2. Уровень вложенности настроек не привышает 2
    (т.е. вложенные настройки не содержат в себе других вложенных настроек).
    """

    def __init__(self, settings_: Mapping = None):
        self.settings = settings_
        self.__validate_settings()

    def __get_first_level_setting(self, item):
        default = DEFAULTS.get(item, None)
        assert default, AssertionError(f"Invalid Schemora setting: {item}")
        value = self.settings.get(item, Empty())
        assert not isinstance(value, Empty), AssertionError(f"{item} Schemora setting is not defined.")
        if isinstance(value, dict):
            return _NestedSetting(value, item, self.settings)
        return value

    def __validate_settings(self):
        for setting_name, setting_value in DEFAULTS.items():
            self.__validate_first_level_required_settings(setting_name, setting_value)
        for setting_name, setting_value in self.settings.items():
            self.__validate_other_settings(setting_name, setting_value)

    def __validate_first_level_required_settings(self, __name, __value):
        if isinstance(__value, RequiredSetting):
            assert not isinstance(getattr(self.settings, __name, Empty()), Empty), AssertionError(
                f"{__name} Schemora setting is required, but not defined."
            )

    def __validate_other_settings(self, __name, __value):
        value = DEFAULTS.get(__name, Empty())
        assert not isinstance(value, Empty), AssertionError(f"Unknown Schemora setting: {__name}")
        for setting_name, setting_value in value.items():
            if isinstance(setting_value, RequiredSetting):
                assert not isinstance(__value.get(setting_name, Empty()), Empty), AssertionError(
                    f"Required subsetting {setting_name} by {__name} Schemora setting is not defined."
                )
            elif isinstance(setting_value, DependentSetting):
                assert setting_value.depended in DEFAULTS.keys(), AssertionError(
                    f"Setting {setting_value.depended} is not valid Schemora setting."
                )

    def __getitem__(self, item):
        return self.__get_first_level_setting(item)

    def __getattr__(self, item):
        return self.__get_first_level_setting(item)


if __name__ == "__main__":
    SCHEMORA_TEST_SETTINGS = {
        "USER_SETTINGS": {
            "USER_SETTINGS_MODEL": "home_app.models.UserSettings",
            "DEFAULT_USER_AVATAR_FILENAME": "default-user-icon.jpg",
            "SERIALIZERS_MODULE": "apiv1.serializers",
            "FORMS_MODULE": "home_app.forms"
        },
        "CACHE": {
            "USER_SETTINGS_CACHE_NAME": "settings",
            "USER_SETTINGS_CACHE_TIMEOUT": 60 * 60 * 24 * 7,
            "USER_DEFINED_CACHE_NAME_DELIMITER": "/"
        }
    }
    schemora_settings = SchemoraSettings(SCHEMORA_TEST_SETTINGS)
    # ... some tests
else:
    schemora_settings = SchemoraSettings(settings)
