#!/bin/sh
export FLASK_APP=app            # flask app to be started (app.py)
export FLASK_ENV=development    # enable additional debugging
export FLASK_DEBUG=1            # set debug level
cd /home/flask                  # go to our home directory
flask run -h 0.0.0.0 -p 5010    # listen to port 5010 on all interfaces
