from datetime import datetime
from typing import Any, Dict, Tuple, Type, Union

import pytz
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.utils.module_loading import import_string

from schemora.cache import get_cache_name_delimiter, get_user_settings_cache_name, get_user_settings_cache_timeout
from schemora.conf import schemora_settings

User = get_user_model()


def get_user_settings_model() -> Type:
    """ Функция для ленивой загрузки модели настроек пользователя. """

    return import_string(schemora_settings.USER_SETTINGS.USER_SETTINGS_MODEL)


UserSettings = get_user_settings_model()


def get_user_settings(user: Union[User | AnonymousUser, UserSettings]) -> UserSettings:
    """ Функция для получения объекта настроек пользователя. """

    if isinstance(user, UserSettings):
        return user
    elif isinstance(user, User):
        settings_cache_name = f"{user.pk}{get_cache_name_delimiter()}{get_user_settings_cache_name()}"
        user_settings = cache.get(settings_cache_name)

        if not user_settings:
            user_settings = UserSettings.objects.get(user=user)
            cache.set(settings_cache_name, user_settings, float(get_user_settings_cache_timeout()))
        return user_settings
    raise TypeError(f"Object {user} is not User instance")


def get_user_timezone(user: User) -> str:
    """ Получение временной зоны пользователя. """

    if isinstance(user, AnonymousUser):
        return schemora_settings.USER_SETTINGS.DEFAULT_USER_TIMEZONE
    return get_user_settings(user).timezone


def get_user_avatar_path(user: User | UserSettings) -> Tuple:
    """
    Получение пути до обрезанного аватара пользователя по ссылке на него
    или по ссылке на объект его настроек.
    """

    user_settings = get_user_settings(user)
    avatar_path = str(user_settings.avatar)
    if avatar_path == str(schemora_settings.USER_SETTINGS.DEFAULT_USER_AVATAR_FILENAME):
        return avatar_path, user_settings
    else:
        return get_upload_crop_path(avatar_path), user_settings


def get_datetime_in_timezone(dt: datetime, timezone: str) -> datetime:
    """ Получение datetime объекта в определенной временной зоне. """

    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return dt + dt.utcoffset()


def get_instance_datetime_attribute(user: User, instance: Any, attribute: str = "time_added") -> Dict[str, str]:
    """ Получение DateTime атрибута объекта в выбранной временной зоне пользователя. """

    assert hasattr(instance, attribute), AttributeError(
        f"Invalid {instance.__class__.__name__} model field: {attribute}"
    )
    dt = getattr(instance, attribute)
    user_timezone = get_user_timezone(user)
    dt = get_datetime_in_timezone(dt, user_timezone)
    return {
        attribute: dt.strftime("%H:%M %d/%m/%Y"),
        "time_zone": user_timezone,
    }


def get_upload_crop_path(path: str) -> str:
    """ Функция для получения пути к центрированному изображению по пути исходного. """

    splitted_path = path.split("/")
    filename = splitted_path.pop()
    name, extension = filename.split(".")
    splitted_path.append(f"{name}_crop.{extension}")
    return "/".join(splitted_path)
