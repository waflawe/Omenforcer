# Форум
Проект простого форума по Django Framework. Проект написан на ЯП Python с использованием Django,
Django REST Framework, Celery + Redis, PostgreSQL.

## Установка
```commandline
git clone https://github.com/waflawe/django-forum.git
cd django-forum
```

### Запуск через Docker
```commandline
docker-compose up
```
Переходим на http://127.0.0.1:80 и наслаждаемся.

### Запуск локально
При локальном запуске вам нужно предварительно создать файл с переменными окружения .env 
по примеру файла .env.docker в репозитории.
```commandline
python -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt
redis-server
```
```commandline
source venv/bin/activate
celery -A forum.celery_setup:app worker --loglevel=info
```
```commandline
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:80
```
Переходим на http://127.0.0.1:80 и наслаждаемся.