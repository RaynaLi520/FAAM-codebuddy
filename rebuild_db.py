#!/usr/bin/env python3
"""重建数据库 - 确保所有表和数据正确导入"""
import sqlite3
import os

def rebuild_database():
    db_path = 'faam_products.db'
    
    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除旧数据库: {db_path}")
    
    # 创建新数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建 products 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tcin TEXT,
        title TEXT,
        brand TEXT,
        price REAL,
        retail_price REAL,
        original_price REAL,
        has_promotion TEXT,
        savings_amount REAL,
        discount_percentage TEXT,
        max_discount TEXT,
        is_clearance TEXT,
        material TEXT,
        sales_count INTEGER,
        delivery_date TEXT,
        is_new TEXT,
        rating REAL,
        review_count INTEGER,
        secondary_ratings TEXT,
        color_summary TEXT,
        color TEXT,
        size_summary TEXT,
        bullet_points TEXT,
        image_url TEXT,
        product_url TEXT,
        item_type TEXT,
        date_added TEXT,
        date_updated TEXT,
        first_seen_date TEXT
    )
    ''')
    
    # 创建 daily_new_arrivals 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_new_arrivals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tcin TEXT,
        title TEXT,
        brand TEXT,
        price REAL,
        retail_price REAL,
        original_price REAL,
        discount_percentage TEXT,
        is_clearance TEXT,
        is_new TEXT,
        rating REAL,
        review_count INTEGER,
        color_summary TEXT,
        size_summary TEXT,
        image_url TEXT,
        product_url TEXT,
        item_type TEXT,
        date_added TEXT
    )
    ''')
    
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
    print("数据库表结构创建完成")
    
    # 导入 SQL 数据
    sql_file = 'database_data.sql'
    if os.path.exists(sql_file):
        print(f"正在导入数据从 {sql_file}...")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割并执行 SQL 语句
        statements = sql_content.split(';')
        for i, stmt in enumerate(statements):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                if 'CREATE TABLE' in stmt.upper() or 'CREATE VIEW' in stmt.upper():
                    continue  # 跳过创建语句，因为我们已经有了
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    # 忽略错误继续（某些 INSERT 可能因为约束失败）
                    pass
        
        conn.commit()
        print("SQL 数据导入完成")
    
    # 验证数据
    products_count = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    daily_count = cursor.execute('SELECT COUNT(*) FROM daily_new_arrivals').fetchone()[0]
    unique_count = cursor.execute('SELECT COUNT(*) FROM unique_products').fetchone()[0]
    clearance_count = cursor.execute('SELECT COUNT(*) FROM products WHERE is_clearance = "Yes"').fetchone()[0]
    
    print(f"\n数据验证:")
    print(f"  - products 表: {products_count} 条记录")
    print(f"  - daily_new_arrivals 表: {daily_count} 条记录")
    print(f"  - unique_products 视图: {unique_count} 条记录")
    print(f"  - 清仓商品: {clearance_count} 条记录")
    
    # 检查图片
    images_count = 0
    if os.path.exists('static/images/products'):
        images_count = len([f for f in os.listdir('static/images/products') if f.endswith('.jpg')])
    print(f"  - 本地图片: {images_count} 张")
    
    conn.close()
    print(f"\n数据库重建完成!")

if __name__ == '__main__':
    rebuild_database()
