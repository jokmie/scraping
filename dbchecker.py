import sqlite3

conn = sqlite3.connect('products.db')
c = conn.cursor()
print("#####TOTAL ROWS#######")
print(c.execute('''select count(*) from PRODUCTS''').fetchone())

#print("######DISTINCT PRODUCTS######")
#print(c.execute('''select distinct(name) from PRODUCTS''').fetchall())

print("######FIRST 3 ROWS######")
print(c.execute('''select * from PRODUCTS limit 3''').fetchmany(3))

#c.close()

# query = f"Select * FROM PRODUCTS  where name='Se og Hør 1 stk'"
# data = c.execute(query).fetchone()
# print(data)