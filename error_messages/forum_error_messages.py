from typing import Dict

from schemora.core.types import ErrorMessage

ModelField = str
FieldsErrors = Dict[ModelField, ErrorMessage]


class _Comments:
    INVALID_COMMENT = "Неверная длина комментария"
    INVALID_UPLOAD = "Неверное изображение"


class _Topics:
    INVALID_ID = "Передан несуществующий идентификатор темы"
    INVALID_TITLE = "Неверная длина заголовка темы"
    INVALID_QUESTION = "Неверная длина вопроса"
    INVALID_UPLOAD = "Неверное изображение"
    INVALID_SECTION = "Несуществующий раздел форума"


TOPICS_ERRORS: FieldsErrors = {
    "id": _Topics.INVALID_ID,
    "topic": _Topics.INVALID_ID,
    "title": _Topics.INVALID_TITLE,
    "question": _Topics.INVALID_QUESTION,
    "upload": _Topics.INVALID_UPLOAD,
    "section": _Topics.INVALID_SECTION
}

COMMENTS_ERRORS: FieldsErrors = {
    "comment": _Comments.INVALID_COMMENT,
    "upload": _Comments.INVALID_UPLOAD
}
