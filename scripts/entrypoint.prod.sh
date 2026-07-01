#!/bin/bash
set -e

echo "Esperando a la base de datos..."
while ! python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    sleep 1
done
echo "Base de datos lista"

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estaticos..."
python manage.py collectstatic --noinput

echo "Iniciando Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --access-logfile - \
    --error-logfile - \
    config.wsgi:application
