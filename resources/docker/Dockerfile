# syntax=docker/dockerfile:1
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade setuptools>=78.1.1 pip && pip install poetry==1.8.5

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

COPY . /app/

EXPOSE 8000

ARG DJANGO_SUPERUSER_PASSWORD
ARG DJANGO_SUPERUSER_EMAIL
ARG DJANGO_SUPERUSER_USERNAME

ENV DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}
ENV DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}
ENV DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME}

RUN mv /app/resources/docker/entrypoint.sh /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "dataspace_backend.wsgi"]