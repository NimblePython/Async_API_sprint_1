FROM python:3.11-slim

WORKDIR /backend

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY pyproject.toml poetry.lock /backend/

RUN apt update \
    && apt install -y gcc \
    && pip install --upgrade pip \
    && pip install "poetry==1.5.1" \
    && poetry config virtualenvs.create false \
    && poetry install --without dev

COPY src /backend/src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker"]
