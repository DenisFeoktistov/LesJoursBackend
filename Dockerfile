FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev nano

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir gunicorn

COPY . /app/

RUN apt-get install -y wget
RUN python manage.py collectstatic --noinput

RUN apt-get update && apt-get install -y nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8000

# Create a Gunicorn config file
RUN echo "forwarded_allow_ips = '*'\nforwarded_for_ips = '*'" > /app/gunicorn.conf.py

CMD service nginx start && python manage.py runserver 0.0.0.0:8000
