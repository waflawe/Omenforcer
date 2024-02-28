from __future__ import annotations
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
from rest_framework.request import Request
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist

from home_app.models import UserSettings, Review, UserReviews
from services.common_utils import DataValidationMixin
from services.user_settings import settings
from services.user_settings_core import Setting, E

from typing import Dict, Literal, NamedTuple, Union, Tuple, Optional


class CheckAndSetSettingsReturn(NamedTuple):
    flag_error: Union[Literal[None], Literal["SUCCESS"], E]
    flag_success: bool


class CheckOnEditionsReturn(NamedTuple):
    an_error_occured: bool
    error_code: Union[Literal[None], Literal["SUCCESS"], E]


class UpdateSettingsMixin(object):
    """ Миксин для обновления настроек пользователя, прописанных в файле services.user_settings. """

    request_host = None   # переменная-источник запроса. Имеет значение RequestHost.APIVIEW или RequestHost.VIEW

    def update_settings(self, user: User, post: Dict, files: Dict) -> CheckAndSetSettingsReturn:
        flag_success = False
        user_settings, data = get_object_or_404(UserSettings, user=user), post | files

        for setting in settings:
            flag = self._process_setting(setting, user_settings, post, files)
            if flag.an_error_occured:
                return CheckAndSetSettingsReturn(flag.error_code, False)
            else:
                if flag.error_code:
                    flag_success = True

        return CheckAndSetSettingsReturn(False, flag_success)

    def _process_setting(self, setting: Setting, user_settings: UserSettings, post: Dict, files: Dict) \
            -> CheckOnEditionsReturn:
        if any((post.get(setting.field.field, False), files.get(setting.field.field, False))):
            if setting.handler.handler().handle(setting, user_settings, post=post, files=files,
                                                request_host=self.request_host):
                return CheckOnEditionsReturn(True, setting.error.error_code)
            return CheckOnEditionsReturn(False, "SUCCESS")
        return CheckOnEditionsReturn(False, None)


class _ReviewOperationPermissionsTemplate:
    def check_perms(self, request: HttpRequest | Request, filter_: Dict) \
            -> Tuple[Review, User] | Tuple[E, Literal[False] | User]:
        try:
            user = User.objects.get(**filter_)
        except (ObjectDoesNotExist, ValueError):
            return E(2), False
        if not request.user.is_authenticated or request.user == user:
            return E(1), user
        return Review.objects.filter(reviewer=request.user, user=user).first(), user


class AddReviewMixin(_ReviewOperationPermissionsTemplate):
    def add_review(self, request: HttpRequest | Request, ids: int, like: Optional[bool] = True) \
            -> Tuple[Literal[None] | E, User]:
        flag, user = self.check_perms(request, {"pk": ids})
        if isinstance(flag, E): return flag, user
        review, created = (flag, False) if flag else (Review.objects.create(reviewer=request.user, user=user), True)
        user_reviews, _ = UserReviews.objects.get_or_create(user=user)
        if review.feedback == like: return E(3), user
        update_value = 1 if created else 2
        review.feedback, user_reviews.rating = like, F("rating") + update_value if like else F("rating") - update_value
        review.save(update_fields=["feedback", "time_added"]), user_reviews.save(update_fields=["rating"])
        return None, user


class DropReviewMixin(_ReviewOperationPermissionsTemplate):
    def drop_review(self, request: HttpRequest, ids: int, **kwargs) -> Tuple[Literal[None] | E, User]:
        flag, user = self.check_perms(request, {"pk": ids})
        if isinstance(flag, E): return flag, user
        if not flag: return E(4), user
        review, user_reviews, _ = flag, *UserReviews.objects.get_or_create(user=user)
        update_value = -1 if review.feedback else 1
        user_reviews.rating = F("rating") + update_value
        user_reviews.save(update_fields=["rating"])
        review.delete()
        return None, user
