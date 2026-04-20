import sqlite3
conn = sqlite3.connect('faam_products.db')
cursor = conn.cursor()

# 检查评论数量字段
cursor.execute('SELECT review_count, title FROM products LIMIT 5')
print('=== 评论数量示例 ===')
for row in cursor.fetchall():
    print(f'{row[0]} - {row[1][:30]}...')

# 检查类别字段
cursor.execute("SELECT item_type, COUNT(*) FROM products WHERE item_type IS NOT NULL AND item_type != '' GROUP BY item_type LIMIT 10")
print('\n=== 类别分布 ===')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')

# 检查图片URL
cursor.execute('SELECT image_url FROM products LIMIT 3')
print('\n=== 图片URL示例 ===')
for row in cursor.fetchall():
    print(row[0])

# 检查表结构
cursor.execute('PRAGMA table_info(products)')
print('\n=== 表结构 ===')
for row in cursor.fetchall():
    print(row[1])

conn.close()
