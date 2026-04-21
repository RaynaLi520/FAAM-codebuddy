#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
下载唯一商品的图片（按标题去重）
"""

import requests
import os
import sqlite3
from urllib.parse import urlparse
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

IMAGE_DIR = 'static/images/products'
os.makedirs(IMAGE_DIR, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Referer': 'https://www.target.com/'
}

def download_image(url, tcin):
    """下载图片到本地"""
    try:
        parsed = urlparse(url)
        path = parsed.path
        filename = os.path.basename(path)
        
        if not filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            filename = f"{tcin}.jpg"
        
        local_path = os.path.join(IMAGE_DIR, filename)
        
        if os.path.exists(local_path):
            return f"/static/images/products/{filename}", True
        
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(local_path, 'wb') as f:
                f.write(resp.content)
            return f"/static/images/products/{filename}", True
        return None, False
    except Exception as e:
        return None, False

def main():
    conn = sqlite3.connect('faam_products.db')
    cur = conn.cursor()
    
    # 获取每个唯一标题的第一个TCIN及其图片
    cur.execute('''
        SELECT p.title, p.tcin, p.image_url
        FROM products p
        INNER JOIN (
            SELECT title, MIN(tcin) as min_tcin
            FROM products
            WHERE image_url LIKE '%scene7.com%'
            GROUP BY title
        ) unique_products ON p.title = unique_products.title AND p.tcin = unique_products.min_tcin
        WHERE p.image_url LIKE '%scene7.com%'
    ''')
    unique_products = cur.fetchall()
    
    print(f"=== 下载 {len(unique_products)} 张唯一商品图片 ===\n")
    
    success = 0
    failed = 0
    title_to_local_url = {}
    
    for i, (title, tcin, image_url) in enumerate(unique_products):
        if i % 50 == 0:
            print(f"进度: {i}/{len(unique_products)}...")
        
        local_url, ok = download_image(image_url, tcin)
        if ok:
            title_to_local_url[title] = local_url
            success += 1
        else:
            failed += 1
        
        time.sleep(0.05)
    
    print(f"\n=== 更新数据库 ===")
    
    # 更新 products 表
    update_count = 0
    for title, local_url in title_to_local_url.items():
        cur.execute('UPDATE products SET image_url = ? WHERE title = ? AND image_url LIKE "%scene7.com%"', 
                   (local_url, title))
        update_count += cur.rowcount
    
    # 更新 daily_new_arrivals 表
    dna_count = 0
    for title, local_url in title_to_local_url.items():
        cur.execute('UPDATE daily_new_arrivals SET image_url = ? WHERE title = ? AND image_url LIKE "%scene7.com%"', 
                   (local_url, title))
        dna_count += cur.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"\n=== 完成 ===")
    print(f"成功下载: {success}")
    print(f"下载失败: {failed}")
    print(f"更新 products 表: {update_count} 条")
    print(f"更新 daily_new_arrivals 表: {dna_count} 条")

if __name__ == '__main__':
    main()
