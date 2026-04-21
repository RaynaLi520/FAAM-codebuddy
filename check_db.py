import sqlite3
conn = sqlite3.connect('faam_products.db')
print('products 表数量:', conn.execute('SELECT COUNT(*) FROM products').fetchone()[0])
print('daily_new_arrivals 表数量:', conn.execute('SELECT COUNT(*) FROM daily_new_arrivals').fetchone()[0])
conn.close()
