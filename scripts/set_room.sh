#!/bin/sh
curl -X POST -H "Content-Type: application/json" -d "{\"description\": \"You have arrived at the entry point to this year\u2019s KringleCon. In front of you you can see a green fence.\",\"name\": \"TheNorthPole_Orientation\"}" -H "Authorization: Basic xyz" https://kringle.info/api/rooms/1
