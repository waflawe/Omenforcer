from django.contrib.auth.models import User
from django import forms
from rest_framework import serializers
from django.db import models

from home_app.models import UserSettings
from forum.settings import DEFAULT_USER_AVATAR_FILENAME, CUSTOM_USER_AVATARS_DIR, BASE_DIR, MEDIA_ROOT

from typing import Literal, Tuple, Union, Type, Dict, Optional, Any
import os

Context = dict
Instance = models.Model
ValidationClass = Union[Type[serializers.ModelSerializer] | Type[forms.ModelForm]]


class RequestHost(object):
    """ Класс для обозначения источника запроса (вьюшка или апи-вьюшка). """

    APIVIEW = "APIVIEW"
    VIEW = "VIEW"


def get_crop_upload_path(path: str) -> str:
    """ Функция для получения пути к центрированному изображению по пути исходного. """

    splitted_path = path.split("/")
    filename = splitted_path.pop()
    name, extension = filename.split(".")
    splitted_path.append(f"{name}_crop.{extension}")
    return "/".join(splitted_path)


def get_user_avatar_path(user: User | UserSettings) -> Tuple:
    """ Получение пути до аватара пользователя по ссылке на него или по ссылке на объект его настроек. """

    user_settings = UserSettings.objects.get(user=user) if isinstance(user, User) else user
    avatar_path = str(user_settings.avatar)
    if avatar_path == DEFAULT_USER_AVATAR_FILENAME:
        return avatar_path, user_settings
    else:
        return get_crop_upload_path(avatar_path), user_settings


def clean_custom_user_avatars_dir(user: User) -> Literal[None]:
    """ Функция для очищения папки с кастомными аватарками пользователя. Используется при обновлении аватарки. """

    path_to_avatar_dir = f"{MEDIA_ROOT}{CUSTOM_USER_AVATARS_DIR}/{user.pk}/"
    try:
        for file in os.listdir(BASE_DIR / path_to_avatar_dir):
            os.remove(os.path.join(BASE_DIR, path_to_avatar_dir, file))
    except FileNotFoundError:
        pass


class DataValidationMixin(object):
    """ Класс для валидации через форму/сериализатор полученной от пользователя информации. """

    validation_class: ValidationClass = None  # ссылка на класс-валидатор, должна быть переопределена

    def validate_received_data(self, data: Dict, files: Dict, instance: Optional[Instance] = None,
                               validation_class: Optional[ValidationClass] = None,
                               serializer_context: Optional[Dict] = None) -> Tuple[Any, bool, Dict]:
        validation_class = validation_class if validation_class else self.validation_class
        validator_object = None

        if issubclass(validation_class, serializers.ModelSerializer):
            data = self.get_data_to_serializer(data, files)
            serializer_context = serializer_context if serializer_context else {}
            validator_object = validation_class(data=data, instance=instance, context=serializer_context)
        elif issubclass(validation_class, forms.ModelForm):
            validator_object = validation_class(data, files, instance=instance)

        if validator_object:
            is_valid = validator_object.is_valid()
            return validator_object, is_valid, getattr(
                validator_object,
                "validated_data" if hasattr(validator_object, "validated_data") else "cleaned_data"
            )
        return None, False, {}

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:  # должен быть переопределен
        """
        При использовании сериализатора в качестве валидатора функция должна возвращать данные,
        передаваемые в инициализатор сериализатора.
        """

        raise NotImplementedError()
