from home_app.forms import UploadAvatarForm
from services.user_settings_core import include_setting, ValidationClasses
from services.user_settings_handlers import TimezoneHandler, AvatarHandler
from apiv1.serializers import UserAvatarSerializer

# Переменная со всеми настройками пользователя.
settings = (
    include_setting(field="timezone", error_code=3, handler=TimezoneHandler),
    include_setting(field="avatar", error_code=1, handler=AvatarHandler,
                    validation_classes=ValidationClasses(UploadAvatarForm, UserAvatarSerializer))
)
