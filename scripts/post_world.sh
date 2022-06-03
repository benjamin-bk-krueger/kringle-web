#!/bin/sh
curl -X POST -H "Content-Type: application/json" -d "@data.json" -H "Authorization: Basic xyz" https://kringle.info/api/worlds
