from schemora.conf import schemora_settings


def get_cache_name_delimiter(): return schemora_settings.CACHE.USER_DEFINED_CACHE_NAME_DELIMITER


def get_user_settings_cache_name(): return schemora_settings.CACHE.USER_SETTINGS_CACHE_NAME


def get_user_settings_cache_timeout(): return schemora_settings.CACHE.USER_SETTINGS_CACHE_TIMEOUT
