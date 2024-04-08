from django import forms
from rest_framework import serializers

from schemora.core.types import ValidationClass, Instance

from typing import Dict, Optional, Tuple, Any


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
