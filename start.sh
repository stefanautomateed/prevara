#!/bin/bash
# Startup script for Railway deployment

# Default port if not set by Railway
PORT=${PORT:-5000}

echo "Starting application on port $PORT"
echo "Environment:"
echo "  PORT=$PORT"
echo "  HEADLESS=$HEADLESS"
echo "  AUTO_START_SCHEDULER=$AUTO_START_SCHEDULER"
echo "  SCHEDULE_TIMES=$SCHEDULE_TIMES"

# Start gunicorn
exec gunicorn --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 2 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app
