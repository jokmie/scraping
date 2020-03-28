# Scraper data crawler

- crawls som urls, dump info to sqlite and csv


## Howto
- git clone
- docker build -t scraper .
- docker run --name scraper scraper 

## get csv file from docker container og rund querys agsinst the table via dbchecker e.g.
- docker exec -it $(docker ps -aqf "name=scraper") bin/bash
- python dbchecker.py
- cat dataset.csv

