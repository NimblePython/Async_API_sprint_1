FROM python:3.10-slim

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt

RUN apt update \
    && apt install -y gcc \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . /opt/app

CMD ["python", "main.py"]
