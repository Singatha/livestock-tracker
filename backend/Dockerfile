FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

FROM base AS development
RUN pip install --no-cache-dir -r requirements-dev.txt
CMD ["/app/entrypoint.sh"]

FROM base AS production
RUN DJANGO_SECRET_KEY=collect-static-build-key python manage.py collectstatic --noinput \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /app/media \
    && chown -R app:app /app
USER app
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind=0.0.0.0:8000"]
