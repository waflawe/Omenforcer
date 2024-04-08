from enum import StrEnum


class RequestHost(StrEnum):
    """ Класс для обозначения источника запроса (вьюшка или апи-вьюшка). """

    APIVIEW = "APIVIEW"
    VIEW = "VIEW"
