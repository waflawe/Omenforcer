from os.path import join
from pathlib import Path
from typing import List

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = int(env("DEBUG"))

ALLOWED_HOSTS: List[str] = env("ALLOWED_HOSTS").split(", ")

INSTALLED_APPS = [
    "forum_app.apps.ForumAppConfig",
    "home_app.apps.HomeAppConfig",
    "apiv1.apps.Apiv1Config",
    "rest_framework",
    "rest_framework.authtoken",
    "djoser",
    'drf_spectacular',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'forum.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [join(BASE_DIR, "templates/")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media'
            ],
        },
    },
]

WSGI_APPLICATION = 'forum.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    }
}

# CELERY
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")

# PROJECT RUNTIME SETTINGS
CUSTOM_USER_AVATARS_DIR = "avatars"
CUSTOM_TOPIC_UPLOADS_DIR = "t_images"
CUSTOM_COMMENT_UPLOADS_DIR = "c_images"

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": CELERY_BROKER_URL,
        "TIMEOUT": 60*60
    }
}

# CACHE VARIABLES NAMES
LAST_JOINED_CACHE_NAME = "last_joined_user"
TOTAL_TOPICS_CACHE_NAME = "total_topics_count"
TOTAL_COMMENTS_CACHE_NAME = "total_comments_count"
AGGREGATE_COUNT_CACHE_NAME = "aggregate_count_topics_in_sections"

# LOGGING = {
#     "version": 1,
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler"
#         }
#     },
#     "loggers": {
#         "django.db.backends": {
#             "handlers": ["console"],
#             "level": env("DJANGO_LOG_LEVEL", default="DEBUG")
#         }
#     }
# }

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = 'static/'
MEDIA_URL = "/media/"
MEDIA_ROOT = 'media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Django Simple Forum",
    'VERSION': '1.1.0'
}

SCHEMORA_SETTINGS = {
    "USER_SETTINGS": {
        "USER_SETTINGS_MODEL": "home_app.models.UserSettings",
        "DEFAULT_USER_AVATAR_FILENAME": "default-user-icon.jpg",
        "SERIALIZERS_MODULE": "apiv1.serializers",
        "FORMS_MODULE": "home_app.forms"
    },
    "CACHE": {
        "USER_SETTINGS_CACHE_NAME": "settings",
        "USER_SETTINGS_CACHE_TIMEOUT": 60 * 60 * 24 * 7,
        "USER_DEFINED_CACHE_NAME_DELIMITER": "/"
    }
}
