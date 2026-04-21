#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 Target 商品页面获取图片
方法1: 从页面 HTML 中提取 JSON 数据中的图片
方法2: 直接从 HTML 中提取 scene7 图片 URL
方法3: 查找 meta og:image
"""

import requests
import re
import sqlite3
import json
import time
from urllib.parse import urljoin


def fetch_image_from_product_url(product_url):
    """从 Target 商品页面获取图片"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        resp = requests.get(product_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None

        # 方法1: 从页面 HTML 中提取 JSON 数据
        # 查找 window.__PRELOADED_STATE__ 或类似的 JSON 数据
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?});', resp.text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                # 尝试提取图片
                if 'product' in data:
                    product = data['product']
                    # 查找各种可能的图片路径
                    for key in ['primaryImageUrl', 'primary_image_url', 'imageUrl', 'image_url']:
                        if key in product:
                            url = product[key]
                            if 'scene7.com' in url:
                                return url
            except json.JSONDecodeError:
                pass

        # 方法2: 直接从 HTML 中提取 scene7 图片
        images = re.findall(r'https://target\.scene7\.com/is/image/Target/[^\"\'>\s]+', resp.text)
        if images:
            # 去重
            unique_images = list(set(images))
            # 返回第一个完整尺寸的图片
            for img in unique_images:
                if '?' in img or 'scene7.com/is/image/Target/GUEST_' in img:
                    # 确保有尺寸参数
                    if '?' not in img:
                        img = img + '?wid=800&hei=800&qlt=80&fmt=jpeg'
                    return img

        # 方法3: 查找 meta og:image
        og_image = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', resp.text)
        if og_image:
            return og_image.group(1)

        og_image2 = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', resp.text)
        if og_image2:
            return og_image2.group(1)

        # 方法4: 查找 data-src 或 src 属性中的 scene7 图片
        data_src = re.findall(r'data-src=["\']([^"\']*scene7[^"\']*)["\']', resp.text)
        if data_src:
            for img in data_src:
                if 'scene7.com' in img and 'GUEST_' in img:
                    return img

    except Exception as e:
        print(f'  请求错误: {e}')

    return None


def main():
    conn = sqlite3.connect('faam_products.db')
    cur = conn.cursor()

    # 找出所有 image_url 为空或无效的记录
    print('=== 查找所有缺少图片的记录 ===')

    # 检查 daily_new_arrivals
    cur.execute('''
        SELECT dna.id, dna.tcin, dna.title, dna.product_url
        FROM daily_new_arrivals dna
        WHERE dna.image_url IS NULL OR dna.image_url = '' OR dna.image_url LIKE '%TCIN%'
    ''')
    missing_dna = cur.fetchall()
    print(f'daily_new_arrivals 中缺少图片: {len(missing_dna)} 条')

    # 检查 products
    cur.execute('''
        SELECT tcin, title, product_url
        FROM products
        WHERE image_url IS NULL OR image_url = '' OR image_url LIKE '%TCIN%'
    ''')
    missing_p = cur.fetchall()
    print(f'products 中缺少图片: {len(missing_p)} 条')

    if not missing_dna and not missing_p:
        print('\n所有图片都已完整!')
        conn.close()
        return

    # 处理 daily_new_arrivals
    if missing_dna:
        print(f'\n=== 开始处理 daily_new_arrivals 的 {len(missing_dna)} 条记录 ===')

        updated_count = 0
        for id, tcin, title, product_url in missing_dna:
            print(f'\n处理 ID:{id}, TCIN:{tcin}')
            print(f'  标题: {title[:50]}...' if len(title) > 50 else f'  标题: {title}')

            image_url = None

            # 1. 尝试从 products 表获取
            cur.execute('SELECT image_url FROM products WHERE tcin = ?', (tcin,))
            row = cur.fetchone()
            if row and row[0] and 'scene7.com' in str(row[0]) and 'GUEST_' in str(row[0]):
                image_url = row[0]
                print(f'  从 products 表获取: {str(image_url)[:50]}...')
            # 2. 尝试从 product_url 获取
            elif product_url and 'target.com' in str(product_url):
                print(f'  从商品链接获取: {product_url}')
                image_url = fetch_image_from_product_url(product_url)

                if image_url:
                    print(f'  获取成功: {image_url[:50]}...')
            # 3. 尝试构建 product_url
            else:
                constructed_url = f'https://www.target.com/p/-/A-{tcin}'
                print(f'  构建链接获取: {constructed_url}')
                image_url = fetch_image_from_product_url(constructed_url)

                if image_url:
                    print(f'  获取成功: {image_url[:50]}...')

            if image_url:
                # 确保 URL 有尺寸参数
                if 'scene7.com' in image_url and 'wid=' not in image_url:
                    base_url = image_url.split('?')[0]
                    image_url = f'{base_url}?wid=800&hei=800&qlt=80&fmt=jpeg'

                cur.execute('UPDATE daily_new_arrivals SET image_url = ? WHERE id = ?', (image_url, id))
                updated_count += 1
            else:
                print('  获取失败')

            time.sleep(0.3)

        print(f'\ndaily_new_arrivals 更新了 {updated_count} 条')

    # 处理 products
    if missing_p:
        print(f'\n=== 开始处理 products 的 {len(missing_p)} 条记录 ===')

        updated_count = 0
        for tcin, title, product_url in missing_p:
            print(f'\n处理 TCIN:{tcin}')
            print(f'  标题: {title[:50]}...' if len(title) > 50 else f'  标题: {title}')

            image_url = None

            # 1. 尝试从 daily_new_arrivals 获取
            cur.execute('SELECT image_url FROM daily_new_arrivals WHERE tcin = ? AND image_url IS NOT NULL AND image_url != ""', (tcin,))
            row = cur.fetchone()
            if row and row[0] and 'scene7.com' in str(row[0]):
                image_url = row[0]
                print(f'  从 daily_new_arrivals 获取: {str(image_url)[:50]}...')
            # 2. 尝试从 product_url 获取
            elif product_url and 'target.com' in str(product_url):
                print(f'  从商品链接获取: {product_url}')
                image_url = fetch_image_from_product_url(product_url)

                if image_url:
                    print(f'  获取成功: {image_url[:50]}...')
            # 3. 尝试构建 product_url
            else:
                constructed_url = f'https://www.target.com/p/-/A-{tcin}'
                print(f'  构建链接获取: {constructed_url}')
                image_url = fetch_image_from_product_url(constructed_url)

                if image_url:
                    print(f'  获取成功: {image_url[:50]}...')

            if image_url:
                # 确保 URL 有尺寸参数
                if 'scene7.com' in image_url and 'wid=' not in image_url:
                    base_url = image_url.split('?')[0]
                    image_url = f'{base_url}?wid=800&hei=800&qlt=80&fmt=jpeg'

                cur.execute('UPDATE products SET image_url = ? WHERE tcin = ?', (image_url, tcin))
                updated_count += 1
            else:
                print('  获取失败')

            time.sleep(0.3)

        print(f'\nproducts 更新了 {updated_count} 条')

    conn.commit()

    # 验证结果
    print('\n=== 验证结果 ===')
    cur.execute('SELECT COUNT(*) FROM daily_new_arrivals WHERE image_url IS NULL OR image_url = "" OR image_url LIKE "%TCIN%"')
    remaining_dna = cur.fetchone()[0]
    print(f'daily_new_arrivals 剩余缺少图片: {remaining_dna} 条')

    cur.execute('SELECT COUNT(*) FROM products WHERE image_url IS NULL OR image_url = "" OR image_url LIKE "%TCIN%"')
    remaining_p = cur.fetchone()[0]
    print(f'products 剩余缺少图片: {remaining_p} 条')

    conn.close()


if __name__ == '__main__':
    main()
