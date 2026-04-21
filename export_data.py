"""
导出数据库数据为 SQL INSERT 语句
用于同步到 Cloud Studio
"""
import sqlite3
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'faam_products.db'

def escape_sql_value(val):
    """转义 SQL 值"""
    if val is None:
        return 'NULL'
    elif isinstance(val, bool):
        return '1' if val else '0'
    elif isinstance(val, (int, float)):
        return str(val)
    else:
        # 字符串，转义单引号
        val_str = str(val).replace("'", "''")
        return f"'{val_str}'"

def export_table(cursor, table_name, columns, output_file):
    """导出单个表的数据"""
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    descriptions = cursor.description
    
    print(f"导出 {table_name}: {len(rows)} 条记录...")
    
    for row in rows:
        values = [escape_sql_value(row[i]) for i in range(len(columns))]
        sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
        output_file.write(sql)

def main():
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库文件 {DB_PATH} 不存在")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    output_file = open('database_data.sql', 'w', encoding='utf-8')
    output_file.write("-- FAAM Database Export\n")
    output_file.write(f"-- Generated at: 2026-04-21\n\n")
    
    # 导出 products 表
    products_columns = [
        'id', 'tcin', 'title', 'brand', 'price', 'retail_price', 'original_price',
        'has_promotion', 'savings_amount', 'discount_percentage', 'max_discount',
        'is_clearance', 'material', 'sales_count', 'delivery_date', 'is_new',
        'rating', 'review_count', 'secondary_ratings', 'color_summary',
        'color', 'size_summary', 'bullet_points', 'image_url', 'product_url',
        'item_type', 'date_added', 'date_updated', 'first_seen_date'
    ]
    export_table(cursor, 'products', products_columns, output_file)
    
    # 导出 daily_new_arrivals 表
    dna_columns = [
        'id', 'tcin', 'title', 'brand', 'price', 'image_url', 'product_url',
        'date_detected', 'is_processed', 'item_type'
    ]
    export_table(cursor, 'daily_new_arrivals', dna_columns, output_file)
    
    output_file.close()
    conn.close()
    
    # 显示文件大小
    size = os.path.getsize('database_data.sql')
    print(f"\n导出完成: database_data.sql ({size / 1024 / 1024:.2f} MB)")
    print(f"总计记录: products + daily_new_arrivals")

if __name__ == '__main__':
    main()
