from django.contrib.auth.models import User

from forum.settings import DEFAULT_USER_AVATAR_FILENAME
from services.schemora.settings import get_user_settings_model

from typing import Tuple

UserSettings = get_user_settings_model()
Context = dict


def get_crop_upload_path(path: str) -> str:
    """ Функция для получения пути к центрированному изображению по пути исходного. """

    splitted_path = path.split("/")
    filename = splitted_path.pop()
    name, extension = filename.split(".")
    splitted_path.append(f"{name}_crop.{extension}")
    return "/".join(splitted_path)


def get_user_avatar_path(user: User | UserSettings) -> Tuple:
    """ Получение пути до обрезанного аватара пользователя по ссылке на него или по ссылке на объект его настроек. """

    user_settings = UserSettings.objects.get(user=user) if isinstance(user, User) else user
    avatar_path = str(user_settings.avatar)
    if avatar_path == DEFAULT_USER_AVATAR_FILENAME:
        return avatar_path, user_settings
    else:
        return get_crop_upload_path(avatar_path), user_settings
