#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入数据库 SQL 文件
"""
import sqlite3
import re

def import_sql(sql_file, db_file):
    # 删除旧数据库
    import os
    if os.path.exists(db_file):
        os.remove(db_file)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割并执行每个语句
    statements = []
    current_stmt = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        
        if line.startswith('DROP') or line.startswith('CREATE') or line.startswith('INSERT'):
            # 如果有正在收集的语句，先保存
            if current_stmt:
                statements.append(' '.join(current_stmt))
                current_stmt = []
            statements.append(line)
        elif current_stmt:
            # 继续收集多行语句
            current_stmt.append(line)
    
    for stmt in statements:
        stmt = stmt.strip().rstrip(';')
        if stmt:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Warning executing: {stmt[:80]}...")
                print(f"  Error: {e}")
                continue
    
    conn.commit()
    conn.close()
    print(f"Database imported: {db_file}")

if __name__ == '__main__':
    import_sql('database_data.sql', 'faam_products.db')
