#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入数据库 SQL 文件（无需 sqlite3 命令行工具）
"""

import sqlite3
import sys

def import_sql(sql_file, db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # 分割 SQL 语句并执行
    statements = sql.split(';')
    
    for stmt in statements:
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--'):
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Warning: {e}")
                continue
    
    conn.commit()
    conn.close()
    print(f"Database imported successfully: {db_file}")

if __name__ == '__main__':
    import_sql('database_data.sql', 'faam_products.db')
