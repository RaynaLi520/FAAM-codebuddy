import sqlite3
conn = sqlite3.connect('faam_products.db')
cur = conn.cursor()

print('=== products 表图片完整性统计 ===')

# 1. 完全为空
cur.execute('SELECT COUNT(*) FROM products WHERE image_url IS NULL OR image_url = ""')
print(f'完全为空: {cur.fetchone()[0]} 条')

# 2. 不含 wid= 参数
cur.execute("SELECT COUNT(*) FROM products WHERE image_url NOT LIKE '%wid=%' AND image_url IS NOT NULL AND image_url != ''")
print(f'不含尺寸参数: {cur.fetchone()[0]} 条')

# 3. 不含 scene7
cur.execute("SELECT COUNT(*) FROM products WHERE image_url NOT LIKE '%scene7%' AND image_url IS NOT NULL AND image_url != ''")
print(f'不含 scene7: {cur.fetchone()[0]} 条')

# 4. 检查是否有图片 URL 格式异常
cur.execute('''
    SELECT tcin, title, image_url 
    FROM products 
    WHERE image_url IS NOT NULL AND image_url != "" AND (
        image_url NOT LIKE '%wid=%' 
        OR image_url NOT LIKE '%scene7%'
    )
    LIMIT 10
''')
print('\n=== 格式异常的图片 ===')
rows = cur.fetchall()
print(f'异常数量: {len(rows)}')
for row in rows[:5]:
    tcin, title, url = row
    print(f'TCIN: {tcin}')
    print(f'  标题: {title[:50]}...' if len(title) > 50 else f'  标题: {title}')
    print(f'  URL: {url[:80]}...' if len(url) > 80 else f'  URL: {url}')

conn.close()
