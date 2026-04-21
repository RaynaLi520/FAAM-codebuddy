import sqlite3
from difflib import SequenceMatcher

conn = sqlite3.connect('faam_products.db')
cur = conn.cursor()

def similarity_ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

# 获取唯一商品的标题列表
cur.execute('SELECT title FROM unique_products')
unique_titles = set(row[0] for row in cur.fetchall())
print(f"唯一商品标题数: {len(unique_titles)}")

# 更新 daily_new_arrivals，只保留唯一商品的记录
cur.execute('SELECT id, title, tcin FROM daily_new_arrivals')
dna_records = cur.fetchall()

# 找出需要删除的记录
to_delete = []
for id, title, tcin in dna_records:
    if title not in unique_titles:
        to_delete.append(id)

print(f"daily_new_arrivals 原始记录数: {len(dna_records)}")
print(f"需要删除的记录数: {len(to_delete)}")

# 删除非唯一商品的记录
if to_delete:
    placeholders = ','.join('?' * len(to_delete))
    cur.execute(f'DELETE FROM daily_new_arrivals WHERE id IN ({placeholders})', to_delete)
    print(f"已删除: {cur.rowcount} 条")

conn.commit()

# 验证
cur.execute('SELECT COUNT(*) FROM daily_new_arrivals')
print(f"daily_new_arrivals 剩余记录数: {cur.fetchone()[0]}")

conn.close()
