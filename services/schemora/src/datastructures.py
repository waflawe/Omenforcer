from services.schemora.src.types import E, ErrorMessage

from typing import NamedTuple, Optional, Type


class Field(NamedTuple):
    """
    Информация о названии настройки.
    """

    field: str


class Error(NamedTuple):
    """ Информация о коде ошибки, связанной с конкретной настройкой, и ее (ошибки) сообщении об ошибке. """

    error_code: E
    error_message: Optional[ErrorMessage] = None


class ValidationClasses(NamedTuple):
    """ Информация о классах-валидаторах определенной настройки на WEB'e и API. """

    web_validation_class: str
    api_validation_class: str


class Handler(NamedTuple):
    """ Информация об обработчике настройки. """

    handler: Type   # ссылка на класс - наследник абстрактного класса schemora.handlers.BaseHandler
    validation_classes: Optional[ValidationClasses] = None


class Setting(NamedTuple):
    """ Класс настройки. """

    field: Field
    error: Error
    handler: Handler

    def __str__(self):
        return f"{self.field.field.capitalize()} field with {self.handler.handler} handler"
