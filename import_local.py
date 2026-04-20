"""
导入本地新品Excel数据到数据库
处理 DISPIMG 格式的图片（无法直接提取），改用 TCIN 构建图片URL
"""
import pandas as pd
import sqlite3
import os
import re
from datetime import datetime

DB_PATH = 'D:/CodeBuddy/FAAM/faam_products.db'
LOCAL_FILE = 'D:/Lingma/mission0415-/FAAM/New_Launched_0311-today(1).xlsx'

def parse_price(value):
    """解析价格字符串"""
    if pd.isna(value):
        return None
    try:
        price_str = str(value).replace('$', '').replace(',', '').strip()
        return float(price_str) if price_str else None
    except:
        return None

def build_image_url_from_tcin(tcin):
    """根据TCIN构建Target图片URL"""
    if not tcin:
        return None
    return f"https://target.scene7.com/is/image/Target/{tcin}?wid=600&hei=600&fmt=jpeg&qlt=80"

def import_local_data():
    """导入本地Excel数据"""
    if not os.path.exists(LOCAL_FILE):
        print(f"文件不存在: {LOCAL_FILE}")
        return 0
    
    df = pd.read_excel(LOCAL_FILE)
    print(f"读取 Excel，共 {len(df)} 行")
    print(f"列名: {list(df.columns)}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    imported = 0
    skipped = 0
    
    for index, row in df.iterrows():
        try:
            tcin = str(row.get('TCIN', '')).strip()
            if not tcin:
                continue
            
            title = str(row.get('标题', ''))
            brand = str(row.get('Brand', row.get('品牌', '')))
            price = parse_price(row.get('价格'))
            
            # 用TCIN构建图片URL
            image_url = build_image_url_from_tcin(tcin)
            
            # 构建购买链接
            product_url = f"https://www.target.com/p/-/A-{tcin}" if tcin else ''
            
            # 检查是否已存在
            cursor.execute('SELECT id FROM daily_new_arrivals WHERE tcin = ?', (tcin,))
            if cursor.fetchone():
                skipped += 1
                continue
            
            cursor.execute('''
                INSERT INTO daily_new_arrivals
                (tcin, title, brand, price, image_url, product_url, date_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (tcin, title, brand, price, image_url, product_url, '2026-03-11'))
            
            imported += 1
            
        except Exception as e:
            print(f"Error on row {index}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n导入完成: {imported} 条新记录")
    print(f"跳过(重复): {skipped} 条")
    return imported

if __name__ == '__main__':
    print("="*50)
    print("导入本地新品数据")
    print("="*50)
    import_local_data()