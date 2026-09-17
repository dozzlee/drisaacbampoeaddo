FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY web-pictures/ /app/seed-pictures/
CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_picture_album && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
