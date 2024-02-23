from services.user_settings_core import Setting, E
from services.common_utils import DataValidationMixin, RequestHost
from home_app.models import UserSettings
from tasks.home_app_tasks import make_center_crop

from typing import Literal, Dict
import pytz


class BaseHandler(object):
    """ Шаблон базового обработчика настройки. """

    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:   # должен быть переопределен
        """
        Метод для обрабатывания настройки. Будет вызван в случае, когда она обновлена.
        В kwargs передаются наборы полученных данных 'post' и 'files'.
        """

        raise NotImplementedError()


class TimezoneHandler(BaseHandler):
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        timezone = kwargs["post"][setting.field.field]
        if timezone not in pytz.common_timezones: return setting.error.error_code
        user_settings.timezone = timezone
        user_settings.save()


class AvatarHandler(BaseHandler, DataValidationMixin):
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        validation_classes = setting.handler.validation_classes
        self.validation_class = (validation_classes.web_validation_class if kwargs["request_host"] == RequestHost.VIEW
                                 else validation_classes.api_validation_class)
        files = {setting.field.field: kwargs["files"][setting.field.field]}
        v, is_valid, data = self.validate_received_data({}, files, instance=user_settings)
        if is_valid:
            obj = v.save()
            make_center_crop.delay(obj.avatar.path)
        else:
            return setting.error.error_code

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:
        return data | files
