#!/bin/bash
sudo -i -u postgres
createuser --interactive
createdb flask

su - flask -s /bin/bash 
psql
ALTER USER flask PASSWORD 'password';
