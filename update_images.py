import sqlite3

conn = sqlite3.connect('faam_products.db')
cursor = conn.cursor()

# 获取所有需要更新的记录
cursor.execute("SELECT id, image_url FROM products WHERE image_url IS NOT NULL AND image_url != '' AND image_url != 'nan'")
rows = cursor.fetchall()

updated = 0
for row_id, url in rows:
    new_url = url
    # 添加 https 前缀
    if new_url.startswith('//'):
        new_url = 'https:' + new_url
    # 添加参数
    if '?' not in new_url:
        new_url = new_url + '?wid=600&hei=600&fmt=jpeg&qlt=80'
    
    cursor.execute('UPDATE products SET image_url = ? WHERE id = ?', (new_url, row_id))
    updated += 1

conn.commit()
print(f'更新了 {updated} 条图片URL')

# 验证
cursor.execute('SELECT image_url FROM products LIMIT 3')
print('\n更新后的图片URL:')
for row in cursor.fetchall():
    print(row[0][:100] + '...' if len(row[0]) > 100 else row[0])

conn.close()