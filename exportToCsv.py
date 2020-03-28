import sqlite3
import csv

conn = sqlite3.connect('products.db')
c = conn.cursor()

data = c.execute('''select * from PRODUCTS''').fetchall()

with open('dataset.csv', mode='w') as datatile:
    employee_writer = csv.writer(datatile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for row in data:
        employee_writer.writerow(row)