FROM python:3.11-slim

RUN mkdir Omenforcer
WORKDIR Omenforcer

ADD requirements/prod.txt /Omenforcer/requirements.txt
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y curl && apt-get clean

ADD . /Omenforcer/
ADD .env.docker /Omenforcer/.env

RUN mkdir log/

CMD sleep 10; python manage.py makemigrations; python manage.py migrate; python manage.py collectstatic --no-input; \
gunicorn forum.wsgi:application -c /Omenforcer/gunicorn.conf.py
