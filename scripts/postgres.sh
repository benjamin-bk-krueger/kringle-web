#!/bin/bash
sudo -i -u postgres
createuser --interactive
createdb flask

su - flask -s /bin/bash 
psql
ALTER USER flask PASSWORD 'password';
\q


pg_dump -F c kringle > kringle.dump
pg_restore -d kringle kringle.dump
pg_restore -U kringle -d kringle tmp/kringle.dump
