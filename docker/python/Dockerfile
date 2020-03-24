FROM python:3.6
MAINTAINER kornel-docker

COPY ./web-scraper /app

WORKDIR /app

RUN pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate
