from schemora.core.datastructures import Setting
from schemora.core.types import E
from schemora.settings.helpers import get_user_settings_model
from schemora.settings.handlers import BaseHandler
from schemora.settings.mixins import BaseDataValidationHandlerMixin

from tasks.home_app_tasks import make_center_crop

from typing import Literal, Dict
import pytz

UserSettings = get_user_settings_model()


class TimezoneHandler(BaseHandler):
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        timezone = kwargs["post"][setting.field.field]
        if timezone not in pytz.common_timezones: return setting.error.error_code
        user_settings.timezone = timezone
        user_settings.save(update_fields=["timezone"])


class AvatarHandlerBase(BaseHandler, BaseDataValidationHandlerMixin):
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        self.received_data.files = {setting.field.field: kwargs["files"][setting.field.field]}
        obj = self.data_validation_update_setting(setting, user_settings, kwargs["request_host"])
        if isinstance(obj, E): return obj
        make_center_crop.delay(obj.avatar.path)

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:
        return data | files


class SignatureHandlerBase(BaseHandler, BaseDataValidationHandlerMixin):
    def handle(self, setting: Setting, user_settings: UserSettings, **kwargs) -> Literal[None] | E:
        self.received_data.data = {setting.field.field: kwargs["post"][setting.field.field]}
        obj = self.data_validation_update_setting(setting, user_settings, kwargs["request_host"])
        if isinstance(obj, E): return obj

    def get_data_to_serializer(self, data: Dict, files: Dict) -> Dict:
        return data | files
