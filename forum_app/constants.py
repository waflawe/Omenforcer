from error_messages.forum_error_messages import ModelField

from typing import Dict


class Sections(object):
    GENERAL = "general"
    TEMPLATES = "templates"
    ORM = "orm"
    TESTING = "testing"
    DRF = "drf"
    CELERY = "celery"
    CHANNELS = "channels"
    DEPLOY = "deploy"

    Sections = (
        (GENERAL, "Общий"),
        (TEMPLATES, "Шаблоны"),
        (ORM, "Django ORM"),
        (TESTING, "Тестирование"),
        (DRF, "DRF"),
        (CELERY, "Celery"),
        (CHANNELS, "Django Channels"),
        (DEPLOY, "Deploy")
    )


class SearchParamsExpressions(object):
    Params: Dict[str, ModelField] = {"title": "title", "question": "question", "username": "author__username"}


dict_sections = {key: value for key, value in Sections.Sections}
