import sqlite3
import requests

conn = sqlite3.connect('faam_products.db')
cur = conn.cursor()

print('=== Test image accessibility ===')
cur.execute('SELECT tcin, image_url FROM products ORDER BY RANDOM() LIMIT 20')
rows = cur.fetchall()

success = 0
failed = 0
for tcin, url in rows:
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True)
        if resp.status_code == 200:
            print(f'[OK] {tcin}')
            success += 1
        else:
            print(f'[FAIL] {tcin}: HTTP {resp.status_code}')
            print(f'  URL: {url[:70]}...')
            failed += 1
    except Exception as e:
        print(f'[FAIL] {tcin}: {str(e)[:50]}')
        print(f'  URL: {url[:70]}...')
        failed += 1

print(f'\nTotal: {success} success, {failed} failed')

conn.close()
