from services.user_settings_core import Setting, E
from services.common_utils import DataValidationMixin, RequestHost, ValidationClass
from home_app.models import UserSettings
from tasks.home_app_tasks import make_center_crop

from typing import Literal, Dict, Optional
import pytz


class BaseHandler(object):
    """ Шаблон базового обработчика настройки. """

    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:   # должен быть переопределен
        """
        Метод для обрабатывания настройки. Будет вызван в случае, когда она обновлена.
        В kwargs передаются наборы полученных данных 'post' и 'files'.
        """

        raise NotImplementedError()

    def get_validation_class(self, setting: Setting, request_host: RequestHost) -> ValidationClass:
        validation_classes = setting.handler.validation_classes
        return (validation_classes.web_validation_class if request_host == RequestHost.VIEW
                else validation_classes.api_validation_class)


class BaseDataValidationHandler(BaseHandler, DataValidationMixin):
    """ Шаблон базового обработчика настройки с использованием DataValidationMixin. """

    class ReceivedData:
        data: Optional[Dict] = None
        files: Optional[Dict] = None

    def __init__(self):
        self.received_data = self.ReceivedData()

    def data_validation_update_setting(self, setting: Setting, user_settings: UserSettings,
                                       request_host: RequestHost) -> object | E:
        data, files = tuple((getattr(self.received_data, attr) if getattr(self.received_data, attr) else dict())
                            for attr in ("data", "files"))
        self.validation_class = self.get_validation_class(setting, request_host)
        v, is_valid, data = self.validate_received_data(data, files, instance=user_settings)
        if is_valid:
            return v.save()
        else:
            return setting.error.error_code


class TimezoneHandler(BaseHandler):
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        timezone = kwargs["post"][setting.field.field]
        if timezone not in pytz.common_timezones: return setting.error.error_code
        user_settings.timezone = timezone
        user_settings.save(update_fields=["timezone"])


class AvatarHandler(BaseDataValidationHandler):
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        self.received_data.files = {setting.field.field: kwargs["files"][setting.field.field]}
        obj = self.data_validation_update_setting(setting, user_settings, kwargs["request_host"])
        if isinstance(obj, E): return obj
        make_center_crop.delay(obj.avatar.path)

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:
        return data | files


class SignatureHandler(BaseDataValidationHandler):
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        self.received_data.data = {setting.field.field: kwargs["post"][setting.field.field]}
        obj = self.data_validation_update_setting(setting, user_settings, kwargs["request_host"])
        if isinstance(obj, E): return obj

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:
        return data | files
