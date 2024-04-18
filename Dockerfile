FROM python:3.11-slim

RUN mkdir django-simple-forum
WORKDIR django-simple-forum

ADD requirements/prod.txt /django-simple-forum/requirements.txt
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y curl && apt-get clean

ADD . /django-simple-forum/
ADD .env.docker /django-simple-forum/.env

RUN mkdir log/

CMD sleep 10; python manage.py makemigrations; python manage.py migrate; python manage.py collectstatic --no-input; \
gunicorn forum.wsgi:application -c /django-simple-forum/gunicorn.conf.py
