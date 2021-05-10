FROM tiangolo/uvicorn-gunicorn:python3.7

LABEL maintainer="Sebastian Ramirez <tiangolo@gmail.com>"

RUN pip install --no-cache-dir fastapi

RUN pip install --no-cache-dir --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib google-auth

RUN pip install --upgrade requests

RUN pip install SQLAlchemy

RUN pip install psycopg2

# COPY ./app /app