#!/usr/bin/env python3
"""正确重建数据库 - 处理 HTML 实体编码"""

import sqlite3
import os
import re
import html

db_path = 'faam_products.db'
sql_file = 'database_data.sql'

def decode_html_entities(text):
    """解码 HTML 实体"""
    if not isinstance(text, str):
        return text
    # 替换常见的 HTML 实体
    text = text.replace('&amp;', '&')
    text = text.replace('&#39;', "'")
    text = text.replace('&quot;', '"')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    # 使用 html.unescape 处理其他实体
    text = html.unescape(text)
    return text

# 删除旧数据库
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"已删除旧数据库: {db_path}")

# 读取 SQL 文件
if not os.path.exists(sql_file):
    print(f"错误: {sql_file} 不存在!")
    exit(1)

with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 处理 HTML 实体编码
sql_content = decode_html_entities(sql_content)

# 创建数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("正在执行 SQL 文件...")

# 使用 executescript 一次性执行（它会正确处理语句）
try:
    cursor.executescript(sql_content)
    conn.commit()
    print("SQL 执行完成")
except Exception as e:
    print(f"执行错误: {e}")

# 验证
try:
    products_count = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    print(f"\nproducts 表: {products_count} 条记录")
    
    # 创建 unique_products 视图
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
    print(f"验证错误: {e}")

conn.close()
print(f"\n数据库重建完成: {db_path}")
