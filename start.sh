#!/usr/bin/env bash
set -e
echo "Starting Gunicorn server..."
# The command runs Gunicorn, binds it to the public port ($PORT provided by Render), 
# and points it to your application instance (app:app).
gunicorn --bind 0.0.0.0:$PORT app:app

