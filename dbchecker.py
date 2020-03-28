import sqlite3

conn = sqlite3.connect('products.db')
c = conn.cursor()
print("#####TOTAL ROWS#######")
print(c.execute('''select count(*) from PRODUCTS''').fetchone())

#print("######DISTINCT PRODUCTS######")
#print(c.execute('''select distinct(name) from PRODUCTS''').fetchall())

print("######DISTINCT PRODUCTS######")
print(c.execute('''select * from PRODUCTS limit 10''').fetchmany(10))

#c.close()

# query = f"Select * FROM PRODUCTS  where name='Se og Hør 1 stk'"
# data = c.execute(query).fetchone()
# print(data)