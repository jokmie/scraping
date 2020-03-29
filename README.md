# Scraper data crawler

- crawls som urls, dump info to sqlite and csv


## Howto
- git clone
- docker build -t scraper .
- docker run --name scraper scraper 

## get csv file from docker container og rund querys against the table via dbchecker e.g.
- docker exec -it $(docker ps -aqf "name=scraper") bin/bash
- docker exec -it $(docker ps -aqf "name=scraper") cat log.txt
- docker exec -it $(docker ps -aqf "name=scraper") python dbchecker.py 
- sudo docker cp $(docker ps -aqf "name=scraper"):dataset.csv . 

## Once you have the csv file you can run the tableau workbook
- TabbisExample.twb
- Alternatively run the app locally with "python main.py"

## Test deployment locally
- dev_appserver.py app.yaml  