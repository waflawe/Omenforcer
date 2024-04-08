from forum.settings import BASE_DIR
from schemora.settings.helpers import get_upload_crop_path

import os
from celery import shared_task
from PIL import Image
from PIL.Image import Image as Im
from typing import Literal


@shared_task
def make_center_crop(applicant_avatar_path: str) -> Literal[None]:
    """ Таска для центрирования аватарки/вложения. """

    _center_crop(Image.open(os.path.join(BASE_DIR / applicant_avatar_path))).save(os.path.join(
        get_upload_crop_path(applicant_avatar_path)
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
