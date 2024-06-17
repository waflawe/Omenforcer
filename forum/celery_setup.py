import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forum.settings')

app = Celery(
    'Omenforcer',
    include=['tasks'],
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)
app.conf.task_routes = {
    "tasks.make_center_crop": {"queue": "main_queue"},
}
app.autodiscover_tasks()
