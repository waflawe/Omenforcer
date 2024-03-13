from django import forms
from rest_framework import serializers

from services.schemora.settings import get_user_settings_model, schemora_settings
from services.schemora.src.types import ValidationClass, Instance, E
from services.schemora.src.datastructures import Setting

from typing import Optional, Dict, Tuple, Any
from importlib import import_module

UserSettings = get_user_settings_model()


class RequestHost(object):
    """ Класс для обозначения источника запроса (вьюшка или апи-вьюшка). """

    APIVIEW = "APIVIEW"
    VIEW = "VIEW"


class DataValidationMixin(object):
    """ Класс для валидации через форму/сериализатор полученной от пользователя информации. """

    validation_class: ValidationClass = None  # ссылка на класс-валидатор, должна быть переопределена

    def validate_received_data(self, data: Dict, files: Dict, instance: Optional[Instance] = None,
                               validation_class: Optional[ValidationClass] = None) -> Tuple[Any, bool, Dict]:
        validation_class = validation_class if validation_class else self.validation_class
        validator_object = None

        if issubclass(validation_class, serializers.ModelSerializer):
            validator_object = validation_class(data=self.get_data_to_serializer(data, files), instance=instance)
        elif issubclass(validation_class, forms.ModelForm):
            validator_object = validation_class(data, files, instance=instance)

        if validator_object:
            is_valid = validator_object.is_valid()
            return validator_object, is_valid, getattr(
                validator_object,
                "validated_data" if hasattr(validator_object, "validated_data") else "cleaned_data"
            )
        raise TypeError(f"Invalid validation class: {validation_class}")

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:  # должен быть переопределен
        """
        При использовании сериализатора в качестве валидатора функция должна возвращать данные,
        передаваемые в инициализатор сериализатора.
        """

        raise NotImplementedError()


class DataValidationHandlerMixin(DataValidationMixin):
    """ Миксин базового обработчика настройки с использованием DataValidationMixin. """

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
        smodule, fmodule = schemora_settings["SERIALIZERS_MODULE"], schemora_settings["FORMS_MODULE"]
        return getattr(import_module(smodule if request_host == RequestHost.APIVIEW else fmodule), validation_class)
