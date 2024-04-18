from __future__ import annotations

from typing import Dict, Literal, NamedTuple, Optional, Tuple, Union

from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.http import HttpRequest
from rest_framework.request import Request

from error_messages.home_error_messages import Ratings
from home_app.models import Review, UserRating
from schemora.cache import get_cache_name_delimiter, get_user_settings_cache_name
from schemora.core.datastructures import Setting
from schemora.core.enums import RequestHost
from schemora.core.types import E, ErrorMessage
from schemora.settings.helpers import get_user_settings_model
from services.user_settings import settings

UserSettings = get_user_settings_model()


class UpdateSettingsReturn(NamedTuple):
    flag_error: Union[Literal[False], ErrorMessage]
    flag_success: bool


class ProcessSettingReturn(NamedTuple):
    an_error_occured: bool
    error_message: Union[Literal[False], Literal[True], ErrorMessage]


def get_rating_operation_error_message(error_code: E) -> ErrorMessage:
    if error_code == 3:
        return Ratings.NOT_CHANGED_REVIEW
    elif error_code == 4:
        return Ratings.REVIEW_EMPTY


class UpdateSettingsMixin(object):
    """ Миксин для обновления настроек пользователя, прописанных в файле services.user_settings. """

    # Переменная-источник запроса. Имеет значение RequestHost.APIVIEW или RequestHost.VIEW
    request_host: RequestHost = None

    def update_settings(self, user: User | AnonymousUser, post: Dict, files: Dict) -> UpdateSettingsReturn:
        flag_success, user_settings = False, UserSettings.objects.select_related("user").get(user=user)

        for setting in settings:
            flag = self._process_setting(setting, user_settings, post, files)
            if flag.an_error_occured:
                return UpdateSettingsReturn(flag.error_message, False)
            elif flag.error_message:
                flag_success = True

        return UpdateSettingsReturn(False, flag_success)

    def _process_setting(self, setting: Setting, user_settings: UserSettings, post: Dict, files: Dict) \
            -> ProcessSettingReturn:
        if any((post.get(setting.field.field, False), files.get(setting.field.field, False))):
            if setting.handler.handler().handle(setting, user_settings, post=post, files=files,
                                                request_host=self.request_host):
                return ProcessSettingReturn(True, setting.error.error_message)
            delimiter = get_cache_name_delimiter()
            cache.delete(f"{user_settings.user.pk}{delimiter}{get_user_settings_cache_name()}")
            return ProcessSettingReturn(False, True)
        return ProcessSettingReturn(False, False)


class _ReviewOperationPermissionsMixin:
    """
    Миксин для проверки прав текущего пользователя на
    добавление/изменение/удаление отзыва на другого форумчанина.
    """

    def check_perms(self, request: HttpRequest | Request, user_identifier: Dict) \
            -> Tuple[Review | Literal[None], User] | Tuple[E, Literal[False] | User]:
        try:
            user = User.objects.get(**user_identifier)
        except (ObjectDoesNotExist, ValueError):
            return E(2), False
        if not request.user.is_authenticated or request.user == user:
            return E(1), user
        return Review.objects.filter(reviewer=request.user, user=user).first(), user


class AddReviewMixin(_ReviewOperationPermissionsMixin):
    """ Миксин для добавления/изменения отзыва. """

    def add_review(self, request: HttpRequest | Request, user_identifier: Dict, like: Optional[bool] = True) \
            -> Tuple[Literal[None] | E, User | Literal[False]]:
        flag, user = self.check_perms(request, user_identifier)
        if isinstance(flag, E):
            return flag, user
        review, created = (flag, False) if flag else (Review.objects.create(reviewer=request.user, user=user), True)
        user_reviews, _ = UserRating.objects.get_or_create(user=user)
        if review.feedback == like:
            return E(3), user
        update_value = 1 if created else 2
        review.feedback, user_reviews.rating = (like, (F("rating") + update_value)
                                                if like else (F("rating") - update_value))
        review.save(update_fields=["feedback", "time_added"])
        user_reviews.save(update_fields=["rating"])
        return None, user


class DropReviewMixin(_ReviewOperationPermissionsMixin):
    """ Миксин для удаления отзыва. """

    def drop_review(self, request: HttpRequest | Request, user_identifier: Dict, **kwargs) \
            -> Tuple[Literal[None] | E, User | Literal[False]]:
        flag, user = self.check_perms(request, user_identifier)
        if isinstance(flag, E):
            return flag, user
        if not flag:
            return E(4), user
        review, user_reviews, _ = flag, *UserRating.objects.get_or_create(user=user)
        update_value = -1 if review.feedback else 1
        user_reviews.rating = F("rating") + update_value
        user_reviews.save(update_fields=["rating"])
        review.delete()
        return None, user


class GetUserReviewsInformationMixin(object):
    """
    Миксин для получения инфомации о рейтинге запрашиваемого пользователя
    и отзыве текущего юзера на запрашиваемого камрада.
    """

    def get_user_reviews_info(self, reviewer: User | AnonymousUser, user: User) -> Dict:
        like = Review.objects.filter(reviewer=reviewer, user=user).first() if reviewer.is_authenticated else None
        return {
            "user_rating": UserRating.objects.get(user=user).rating,
            "reviews_count": Review.objects.filter(user=user).count(),
            "like": ("Лайк" if like.feedback else "Дизлайк") if like else None,
        }
