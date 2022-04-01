#!/bin/sh
export FLASK_APP=app
export FLASK_ENV=development
cd /root
flask run -h 0.0.0.0 -p 5010
