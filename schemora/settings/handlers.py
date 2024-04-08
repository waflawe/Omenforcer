from schemora.settings.helpers import get_user_settings_model
from schemora.core.types import E
from schemora.core.datastructures import Setting

from abc import ABC, abstractmethod
from typing import Literal

UserSettings = get_user_settings_model()


class BaseHandler(ABC):
    """ Шаблон базового обработчика настройки. """

    @abstractmethod
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        """
        Метод для обрабатывания настройки. Будет вызван в случае, когда она обновлена.
        В kwargs передаются наборы полученных от пользователя данных 'post' и 'files'.
        """

        raise NotImplementedError()
