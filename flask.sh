#!/bin/sh
export FLASK_APP=app            # flask app to be started (app.py)
export FLASK_ENV=development    # enable additional debugging
export FLASK_DEBUG=1            # set debug level

export POSTGRES_URL="kringle_database:5432"   # PostgreSQL connection data
export POSTGRES_USER="postgres"
export POSTGRES_PW="postgres"
export POSTGRES_DB="postgres"

cd /home/flask                  # go to our home directory
flask run -h 0.0.0.0 -p 5010    # listen to port 5010 on all interfaces
