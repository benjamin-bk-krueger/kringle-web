#!/bin/sh
export FLASK_APP=app
export FLASK_ENV=development
cd /home/flask
flask run -h 0.0.0.0 -p 5010
