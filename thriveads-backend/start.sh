#!/bin/bash

# Railway startup script for ThriveAds Backend
# This script handles the PORT environment variable properly

set -e  # Exit on any error

# Set default port if not provided
PORT=${PORT:-8000}

echo "Starting ThriveAds Backend on port $PORT"
echo "Environment: ${ENVIRONMENT:-development}"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    echo "Please ensure PostgreSQL addon is connected in Railway"
    exit 1
fi

echo "Database URL configured: ${DATABASE_URL%%@*}@***"

# Wait for database to be ready (Railway sometimes needs this)
echo "Waiting for database to be ready..."
python -c "
import time
import psycopg2
import os
from urllib.parse import urlparse

url = urlparse(os.environ['DATABASE_URL'])
max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:]
        )
        conn.close()
        print('Database is ready!')
        break
    except psycopg2.OperationalError as e:
        retry_count += 1
        print(f'Database not ready (attempt {retry_count}/{max_retries}): {e}')
        time.sleep(2)
else:
    print('Database connection failed after all retries')
    exit(1)
"

# Run database migrations
echo "Running database migrations..."
if ! alembic upgrade head; then
    echo "ERROR: Database migrations failed"
    echo "This might be the first deployment. Trying to create tables..."
    # If migrations fail, try to create the database schema
    python -c "
from app.core.database import engine, Base
from app.models import client, campaign, ad, metrics
print('Creating database tables...')
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
fi

# Start the application
echo "Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
