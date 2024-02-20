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
    Params = {"search_in_title": "title", "search_in_question": "question", "search_in_username": "author__username"}


dict_sections = {key: value for key, value in Sections.Sections}
