import requests
import re
import json
import sqlite3
import time
import random
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_product_data_from_target(tcin):
    """Fetch product data from Target website"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    product_url = f'https://www.target.com/p/-/A-{tcin}'

    try:
        resp = requests.get(product_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None

        result = {
            'tcin': tcin,
            'title': '',
            'image_url': '',
            'item_type': '',
        }

        # Extract images
        images = re.findall(r'https://target\.scene7\.com/is/image/Target/GUEST_[a-f0-9-]+', resp.text)
        if images:
            result['image_url'] = images[0]

        # Extract title
        og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', resp.text)
        if og_title:
            result['title'] = og_title.group(1)

        if not result['title']:
            title_match = re.search(r'"title"\s*:\s*"([^"]+)"', resp.text)
            if title_match:
                result['title'] = title_match.group(1)

        # Extract item_type
        item_type_match = re.search(r'"item_type"\s*:\s*"([^"]+)"', resp.text)
        if item_type_match:
            result['item_type'] = item_type_match.group(1)

        return result if result['image_url'] else None

    except Exception as e:
        return None

def main():
    conn = sqlite3.connect('faam_products.db')
    cur = conn.cursor()

    print('=== Sync products missing images from Target ===')

    # Get products with missing or invalid images
    cur.execute('''
        SELECT tcin, title FROM products 
        WHERE image_url IS NULL OR image_url = '' OR image_url NOT LIKE '%scene7%'
    ''')
    products = cur.fetchall()
    total = len(products)

    print(f'Products needing sync: {total}')

    if total == 0:
        print('All products have valid images!')
        conn.close()
        return

    updated = 0
    failed = 0

    for i, (tcin, title) in enumerate(products, 1):
        if i % 20 == 0 or i == 1:
            print(f'Progress: {i}/{total}')

        data = get_product_data_from_target(tcin)
        if data and data.get('image_url'):
            cur.execute('''
                UPDATE products SET
                    title = CASE WHEN ? IS NOT NULL AND ? != '' THEN ? ELSE title END,
                    image_url = CASE WHEN ? IS NOT NULL AND ? != '' THEN ? ELSE image_url END,
                    item_type = CASE WHEN ? IS NOT NULL AND ? != '' THEN ? ELSE item_type END
                WHERE tcin = ?
            ''', (
                data.get('title'), data.get('title'), data.get('title'),
                data.get('image_url'), data.get('image_url'), data.get('image_url'),
                data.get('item_type'), data.get('item_type'), data.get('item_type'),
                tcin
            ))
            updated += 1
        else:
            failed += 1

        time.sleep(random.uniform(0.3, 0.6))

    conn.commit()
    print(f'\n=== Done: {updated} updated, {failed} failed ===')

    conn.close()

if __name__ == '__main__':
    main()
