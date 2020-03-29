# -*- coding: utf-8 -*-
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import logging
import multiprocessing
import time
from base64 import b64decode
from flask import Flask
from flask import jsonify
import csv
import yaml
from threading import Thread

app = Flask(__name__)

def getCursor():
    conn = sqlite3.connect('products.db')
    return conn.cursor()

#@app.before_first_request
@app.route('/startscript/')
def runscript():
    ## Aviod request failing due to too many retires
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    ## DB CON // TEMP SQLITE
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS PRODUCTS_STAGING
                (timestamp text, name text, price real, unitprice text, category text, propterties text)''')
   
    ## GET CONFIG
    def get_config():
        # Load config yaml
        with open('config.yml', 'r') as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        return config

    ## VARIABLES
    headers = {'User-Agent': get_config()['connection']['useragent']}
    pagebase = b64decode(get_config()['connection']['url']).decode("utf-8")
    logging.basicConfig(filename="log.txt",level=logging.INFO, filemode='w')
    logger = logging.getLogger("main")
    logger.info("start: "+str(datetime.now()))
    
    def getAllSiteUrls():
        try:
            pageTree= requests.get(pagebase+"/produkter/", headers=headers).text           
            pageSoup = BeautifulSoup(pageTree,'html.parser')
            productSites= pageSoup.find("ul", {"class":"list-unstyled"}).find_all("li", {"class":"parent-category"})
            allsiteurls = [item.a['href'] for item in productSites if "kategorier" in item.a['href']]## Subpages such as /kategorier/26-kjott-og-kylling/
            return allsiteurls ## antakelse kun kategorier
        except requests.exceptions.ConnectionError:
            r.status_code = "Connection refused"

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
        writeToCsv()

    def writeToCsv():
        data = c.execute('''select * from PRODUCTS''').fetchall()
        with open('dataset.csv', mode='w') as datatile:
            employee_writer = csv.writer(datatile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in data:
                employee_writer.writerow(row)

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
    delta_hour = datetime.now().hour-1
    while True:
        current_hour = datetime.now().hour
        if delta_hour != current_hour:
            logger.info("Start working")
            print("Start working")
            runScriptMulitprocess()
        else:
            logger.info("Wait 60 seconds...")
            print("Wait 60 seconds")
        delta_hour = current_hour
        time.sleep(60)

@app.route('/getsomerows/')
def getsomerows():
    somerows = getCursor().execute('''select * from PRODUCTS limit 3''').fetchmany(3)
    return jsonify(somerows), 200

@app.route('/getrowcount/')
def getrowcount():
    allrows = getCursor().execute('''select count(*) from PRODUCTS''').fetchone()
    return jsonify(allrows), 200

@app.route('/getallrows/')
def getallrows():
    allrows = getCursor().execute('''select * from PRODUCTS''').fetchall()
    return jsonify(allrows), 200

@app.route('/livecheck/')
def liveCheck():
    return 'I´m alive', 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)


############IMPROVEMENTS
## TODO: sitemap
## TODO: TRAVIS
## TODO: Cron
## TODO: Kubernetes
## TODO: Other DB
## TODO: Secrets + config i google
## TODO: min/max instances
## TODO: Hent basis info fra produkt-kategorisiden
## TODO: Max retries exceeded with url: /produkter/27217-masalamagic-nirus-handlagde-hvitoksnan/
## TODO: Flask endpoints
## TODO: Try catch


# FOR LATER 
#####UPDATE OR INSERT
# qry_findByName = f"Select * FROM PRODUCTS  where name='{name}'"
# existingRecored = c.execute(qry_findByName).fetchone()
# if existingRecored != None:
#     if data[2] != price | data[3] != unitprice | data[4] != category | data[5] != propsstring:
#         qry_delete = f"DELETE FROM PRODUCTS WHERE name='{name}'"
#         c.execute(qry_delete)
#         conn.commit()