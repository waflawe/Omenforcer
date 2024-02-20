from forum.settings import BASE_DIR
from services.common_mixins import get_crop_upload_path

import os
from celery import shared_task
from PIL import Image
from PIL.Image import Image as Im
from typing import Literal


@shared_task
def make_center_crop(applicant_avatar_path) -> Literal[None]:
    _center_crop(Image.open(os.path.join(BASE_DIR / applicant_avatar_path))).save(os.path.join(
        get_crop_upload_path(applicant_avatar_path)
    ))


def _center_crop(img: Im) -> Im:
    width, height = img.size
    if width / height == 1:
        return img

    left = (width - min(width, height)) / 2
    top = (height - min(width, height)) / 2
    right = (width + min(width, height)) / 2
    bottom = (height + min(width, height)) / 2

    return img.crop((int(left), int(top), int(right), int(bottom)))


@shared_task
def make_something2(string: str) -> str:
    return string + "ed"


@shared_task
def make_something1(string: str) -> str:
    return string + "!"


@shared_task
def make_something3(string: str) -> str:
    return string + "???"
