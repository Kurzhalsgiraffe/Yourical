FROM python:3.11.3-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt update && \
    apt upgrade -y && \
    apt install -y build-essential python-dev nano procps

RUN pip install --upgrade pip

COPY . /usr/src/app/

RUN pip install -r requirements.txt
