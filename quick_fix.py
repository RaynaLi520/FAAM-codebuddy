#!/usr/bin/env python3
"""简化版数据库重建 - 直接创建缺失的视图"""

import sqlite3
import os

db_path = 'faam_products.db'

if not os.path.exists(db_path):
    print("错误: 数据库文件不存在!")
    print("请先运行: python3 rebuild_db.py")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查 products 表
try:
    count = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    print(f"products 表: {count} 条记录")
except Exception as e:
    print(f"错误: {e}")
    conn.close()
    exit(1)

# 创建 unique_products 视图
try:
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS unique_products AS
    SELECT * FROM products
    WHERE id IN (
        SELECT MIN(id) FROM products
        GROUP BY title
    )
    ''')
    conn.commit()
    unique_count = cursor.execute('SELECT COUNT(*) FROM unique_products').fetchone()[0]
    print(f"unique_products 视图: {unique_count} 条记录")
except Exception as e:
    print(f"视图已存在或创建失败: {e}")

# 检查数据完整性
print("\n数据检查:")
for col in ['price', 'retail_price', 'original_price', 'image_url', 'is_clearance', 'is_new']:
    try:
        has_data = cursor.execute(f'SELECT COUNT(*) FROM products WHERE {col} IS NOT NULL').fetchone()[0]
        print(f"  - {col}: {has_data} 条非空")
    except:
        print(f"  - {col}: 列不存在")

conn.close()
print("\n完成!")
