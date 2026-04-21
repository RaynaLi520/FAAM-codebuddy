import sqlite3
import json

conn = sqlite3.connect('faam_products.db')
cursor = conn.cursor()

def escape_sql(val):
    """安全地转义 SQL 字符串值"""
    if val is None:
        return 'NULL'
    elif isinstance(val, (int, float)):
        return str(val)
    else:
        # 转义单引号
        return "'" + str(val).replace("'", "''").replace("\\", "\\\\") + "'"

with open('database_data.sql', 'w', encoding='utf-8') as f:
    # Products table
    cursor.execute('SELECT * FROM products')
    columns = [desc[0] for desc in cursor.description]
    f.write('-- Products table\n')
    f.write('DROP TABLE IF EXISTS products;\n')
    f.write('CREATE TABLE products (' + ', '.join(columns) + ');\n')
    
    for row in cursor.fetchall():
        values = [escape_sql(v) for v in row]
        f.write('INSERT INTO products VALUES (' + ', '.join(values) + ');\n')
    
    # Unique products table
    cursor.execute('SELECT * FROM unique_products')
    columns = [desc[0] for desc in cursor.description]
    f.write('\n-- Unique products table (deduplicated)\n')
    f.write('DROP TABLE IF EXISTS unique_products;\n')
    f.write('CREATE TABLE unique_products (' + ', '.join(columns) + ');\n')
    
    for row in cursor.fetchall():
        values = [escape_sql(v) for v in row]
        f.write('INSERT INTO unique_products VALUES (' + ', '.join(values) + ');\n')
    
    # Daily new arrivals table
    cursor.execute('SELECT * FROM daily_new_arrivals')
    columns = [desc[0] for desc in cursor.description]
    f.write('\n-- Daily new arrivals table\n')
    f.write('DROP TABLE IF EXISTS daily_new_arrivals;\n')
    f.write('CREATE TABLE daily_new_arrivals (' + ', '.join(columns) + ');\n')
    
    for row in cursor.fetchall():
        values = [escape_sql(v) for v in row]
        f.write('INSERT INTO daily_new_arrivals VALUES (' + ', '.join(values) + ');\n')

conn.close()
print("Database exported to database_data.sql")
