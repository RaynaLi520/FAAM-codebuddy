import sqlite3
from difflib import SequenceMatcher

conn = sqlite3.connect('faam_products.db')
cur = conn.cursor()

def similarity_ratio(a, b):
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a, b).ratio()

# 获取所有产品
cur.execute('''
    SELECT tcin, title, color_summary, size_summary, retail_price, item_type, 
           image_url, brand, product_url, rating, review_count
    FROM products
''')
all_products = cur.fetchall()

print(f"总产品数: {len(all_products)}")

# 按标题分组
title_groups = {}
for p in all_products:
    tcin, title = p[0], p[1]
    title_groups.setdefault(title, []).append(p)

print(f"不同标题数: {len(title_groups)}")

# 进一步按颜色和尺码汇总相似度去重
def is_same_product(p1, p2):
    """判断两个产品是否视为同一商品"""
    # 标题必须完全相同
    if p1[1] != p2[1]:
        return False
    
    c1, c2 = p1[2] or '', p2[2] or ''
    s1, s2 = p1[3] or '', p2[3] or ''
    
    # 计算颜色和尺码汇总的相似度
    color_sim = similarity_ratio(c1, c2)
    size_sim = similarity_ratio(s1, s2)
    
    # 如果相似度 > 0.8，视为同一商品
    return color_sim > 0.8 and size_sim > 0.8

# 去重
unique_products = []
processed = set()

for title, products in title_groups.items():
    if len(products) == 1:
        unique_products.append(products[0])
        processed.add(products[0][0])
    else:
        # 找出主要版本（保留评级最高的）
        best = max(products, key=lambda x: (x[9] or 0, x[10] or 0))
        unique_products.append(best)
        processed.add(best[0])

print(f"去重后唯一商品数: {len(unique_products)}")

# 保存唯一商品到新表
conn.execute('DROP TABLE IF EXISTS unique_products')
conn.execute('''
    CREATE TABLE unique_products (
        tcin TEXT PRIMARY KEY,
        title TEXT,
        color_summary TEXT,
        size_summary TEXT,
        retail_price REAL,
        item_type TEXT,
        image_url TEXT,
        brand TEXT,
        product_url TEXT,
        rating REAL,
        review_count INTEGER
    )
''')

for p in unique_products:
    conn.execute('''
        INSERT INTO unique_products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', p)

conn.commit()

# 验证
cur.execute('SELECT COUNT(*) FROM unique_products')
print(f"唯一商品表记录数: {cur.fetchone()[0]}")

conn.close()
