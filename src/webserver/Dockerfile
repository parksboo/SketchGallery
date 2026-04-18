FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY images /app/images

WORKDIR /app/src

EXPOSE 5050

CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:5050", "webserver.app:create_app()"]
