from schemora.core.datastructures import Setting, Field, Error, Handler
from schemora.core.types import E, ErrorMessage


def include_setting(*args, **kwargs) -> Setting:
    """ Функция для подключения в Schemor'у новой настройки. """

    return Setting(
        Field(kwargs["field"]),
        Error(E(kwargs["error_code"]), ErrorMessage(kwargs.get("error_message", None))),
        Handler(kwargs["handler"], kwargs.get("validation_classes", None))
    )
