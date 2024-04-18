from error_messages.home_error_messages import Settings
from schemora.core.datastructures import ValidationClasses
from schemora.settings import include_setting
from services.user_settings_handlers import AvatarHandlerBase, SignatureHandlerBase, TimezoneHandler

# Переменная со всеми настройками пользователя.
settings = (
    include_setting(field="timezone", error_code=3, error_message=Settings.INVALID_TIMEZONE, handler=TimezoneHandler),
    include_setting(field="avatar", error_code=1, error_message=Settings.INVALID_AVATAR, handler=AvatarHandlerBase,
                    validation_classes=ValidationClasses("UploadAvatarForm", "UserAvatarSerializer")),
    include_setting(
        field="signature", error_code=2, error_message=Settings.INVALID_SIGNATURE, handler=SignatureHandlerBase,
        validation_classes=ValidationClasses("ChangeSignatureForm", "SignatureSerializer")
    )
)
