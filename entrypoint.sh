#!/bin/sh
set -e

DB_FILE="/data/app.db"

# Seed the database on first run only; persisted via the /data volume.
if [ ! -f "$DB_FILE" ]; then
    echo "Database not found. Running seed.py..."
    python seed.py
    echo "Seeding complete."
else
    echo "Database exists. Skipping seed."
fi

# Production WSGI server. create_app() is the factory from app.py.
exec gunicorn --bind 0.0.0.0:5000 --workers 2 "app:create_app()"
