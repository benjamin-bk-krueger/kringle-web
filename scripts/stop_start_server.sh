#!/bin/sh
. ~/.profile
echo "Starting..."

# Stop server
killall /usr/bin/python3

# Pull current GIT repo
cd /home/kringle/git/kringle-web/
git pull

# Purge and copy files to target folders
rm -rf /home/kringle/templates/*
rm -rf /home/kringle/static/*
rm -rf /home/kringle/docs/*

cp -v *.py *.sh *.yml /home/kringle/
cp -v templates/* /home/kringle/templates/
cp -v static/* /home/kringle/static/
cp -vr docs/* /home/kringle/docs/
git log -1 > /home/kringle/gitlog.txt

# Update mkdocs files
cd /home/kringle/
mkdocs build

# Start server
nohup ./flask.sh >/dev/null 2>&1 &
sleep 5
echo "Finished."
