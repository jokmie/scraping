# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import numpy as np
import sqlite3
from datetime import datetime
import logging
import multiprocessing
import time
from base64 import b64decode
import exportToCsv

## DB CON // TEMP SQLITE
conn = sqlite3.connect('products.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS PRODUCTS_STAGING
             (timestamp text, name text, price real, unitprice text, category text, propterties text)''')

## VARIABLES
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
pagebase = b64decode('aHR0cHM6Ly9rb2xvbmlhbC5ubw==').decode("utf-8")
logging.basicConfig(filename="log.txt",level=logging.INFO, filemode='w')
logger = logging.getLogger("main")
logger.info("start: "+str(datetime.now()))

## GET ALL PRODUCT CATEGORY SITE URLS
def getAllSiteUrls():
    pageTree= requests.get(pagebase+"/produkter/", headers=headers).text
    pageSoup = BeautifulSoup(pageTree,'html.parser')
    productSites= pageSoup.find("ul", {"class":"list-unstyled"}).find_all("li", {"class":"parent-category"})
    allsiteurls = [item.a['href'] for item in productSites if "kategorier" in item.a['href']]## Subpages such as /kategorier/26-kjott-og-kylling/
    return allsiteurls ## antakelse kun kategorier

def getProductDetails(url):
    ## GET ALL PRODUCT DETAILS SITE URLS
    pageTreeProducts = requests.get(pagebase+url, headers=headers).text
    pageSoupProducts = BeautifulSoup(pageTreeProducts,'html.parser')
    productListItem = pageSoupProducts.find_all("div", {"class":"product-list-item"})
    allproductUlrs = [item.a['href'] for item in productListItem]

    ## GET DETAILS FOR EVERY PRODUCT
    for product in allproductUlrs:
        pageTreeProduct = requests.get(pagebase+product, headers=headers).text
        pageSoupProduct = BeautifulSoup(pageTreeProduct,'html.parser')

        ## productDetails
        productDetails = pageSoupProduct.find("div", {"class":"product-detail"})
        name = productDetails.h1.find("span", {"itemprop":"name"}).text.lstrip().replace('\n', ' ').replace('\r', '').replace('  ','').replace('\'','"') #name /// ['Hellstrøms Økologisk Svinenakke uten Ben', '0,5 kg  ']
        price = productDetails.find("div", {"class":"price"}).get('content')
        unitprice = productDetails.find("div", {"class":"unit-price"}).text.lstrip().rstrip() #ingredients = productDetails.find("td", {"class":"ingredients-list"}).text.lstrip().rstrip()
        category = productDetails.find("ol", {"class":"breadcrumb"}).text.replace('Alle varer','').lstrip().replace('\n', ' ').replace('\r', '').replace('    ',' >').replace('\'','"')
        ## productDescTable
        productDescTable = productDetails.find("div", {"role": "tabpanel"})

        props = []
        for tr in productDescTable.find_all("tr"):
            if 'th' in str(tr):
                prop = tr.find('th').text.lstrip().rstrip()
                value = tr.find('td').text.lstrip().rstrip().replace('Les mer...','').replace('\n', ' ').replace('\r', '').replace('  ','')
                props.append(prop+':'+value)

        propsstring = str(props).replace('\'','"')
        ### Insert into DB
        query = f"INSERT INTO PRODUCTS_STAGING VALUES ('{str(datetime.now())}','{str(name)}',{str(price)},'{str(unitprice)}','{category}','{propsstring}')"
        c.execute(query)
        conn.commit()
    logger.info(f"Stopped worker for {url}.")
    return

## Clean up in the data
def generateDistinctRowsHelper():
    c.execute('''CREATE TABLE IF NOT EXISTS PRODUCTS
                (timestamp text, name text, price real, unitprice text, category text, propterties text)''')
    c.execute('''DELETE FROM PRODUCTS''')
    conn.commit()
    c.execute('''INSERT INTO PRODUCTS SELECT MAX(timestamp), name, price, unitprice, category, propterties FROM PRODUCTS_STAGING GROUP BY name, price, unitprice, category, propterties''')
    c.execute('''DELETE FROM PRODUCTS_STAGING''')
    conn.commit()
    exportToCsv

def runScriptMulitprocess():
    allsiteurls = getAllSiteUrls()
    allproductUlrs = []
    jobs = []
    for url in allsiteurls:
        process = multiprocessing.Process(target=getProductDetails, args=([url]))
        jobs.append(process)
        logger.info(f"Added worker for {url} to queue.")
        process.start()

    # Wait for all to complete before continuing
    for job in jobs:
        job.join() 
    generateDistinctRowsHelper()
    logger.info("stop: "+str(datetime.now()))


# RUN SCRIPT EVERY OUR / CHECK EVERY 60 SECONDS
delta_hour = 0
while True:
    now_hour = datetime.now().hour
    if delta_hour != now_hour:
        logger.info("Start working")
        print("Start working")
        runScriptMulitprocess()
    else:
        logger.info("Wait 60 seconds...")
        print("Wait 60 seconds")
    delta_hour = now_hour
    time.sleep(60)


## TODO: sitemap
## TODO: logging
## TODO: Kubernetes
## TODO: TRAVIS
## TODO: Pip freeze
## TODO: Docker container
## TODO: Other DB
## TODO: Secrets + config i google
## TODO: unngå dobbel-insert
## TODO: Hent basis info fra produkt-kategorisiden



# FOR LATER UPDATE OR INSERT
## INSERT RECORDS
# qry_findByName = f"Select * FROM PRODUCTS  where name='{name}'"
# existingRecored = c.execute(qry_findByName).fetchone()
# if existingRecored != None:
#     if data[2] != price | data[3] != unitprice | data[4] != category | data[5] != propsstring:
#         qry_delete = f"DELETE FROM PRODUCTS WHERE name='{name}'"
#         c.execute(qry_delete)
#         conn.commit()