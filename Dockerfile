FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home --home-dir /home/app app
COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .

# collectstatic memuat settings, jadi butuh env dummy. Nilai ini hanya
# berlaku untuk perintah ini dan tidak tersimpan di image.

RUN SECRET_KEY=build-only DEBUG=False \
    DB_NAME=x DB_USER=x DB_PASSWORD=x DB_HOST=x DB_PORT=5432 \
    python manage.py collectstatic --noinput

USER app

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
