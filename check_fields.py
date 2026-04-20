import sqlite3
conn = sqlite3.connect('faam_products.db')
cursor = conn.cursor()

# 检查评论数量
cursor.execute('SELECT review_count, rating, title FROM products WHERE review_count IS NOT NULL LIMIT 5')
print('=== 评论数量示例 ===')
for row in cursor.fetchall():
    print(f'review_count={row[0]}, rating={row[1]}, title={row[2][:30]}')

# 检查类别
cursor.execute("SELECT item_type, COUNT(*) FROM products WHERE item_type IS NOT NULL AND item_type != '' GROUP BY item_type LIMIT 10")
print('\n=== 类别分布 ===')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')

conn.close()