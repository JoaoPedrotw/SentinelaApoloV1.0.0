#!/usr/bin/env bash
# entrypoint.prod.sh

set -e

echo "==> Aguardando PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 1
done

echo "==> Executando collectstatic..."
python manage.py collectstatic --noinput

echo "==> Executando migrate..."
python manage.py migrate --noinput


# Inicia o monitoramento em segundo plano
echo "==> Iniciando monitorador_de_rede..."
python manage.py monitorador_de_rede &

echo "==> Iniciando Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 SentinelaApolo.wsgi:application