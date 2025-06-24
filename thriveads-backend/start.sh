#!/bin/bash

# Railway startup script for ThriveAds Backend
# This script handles the PORT environment variable properly

# Set default port if not provided
PORT=${PORT:-8000}

echo "Starting ThriveAds Backend on port $PORT"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
