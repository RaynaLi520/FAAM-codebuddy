import requests
import re
import sqlite3

tcin = '95278689'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

print('=== 尝试直接访问产品页面 ===')
url = f'https://www.target.com/p/-/A-{tcin}'
resp = requests.get(url, headers=headers, timeout=15)
print(f'状态码: {resp.status_code}')

images = re.findall(r'https://target\.scene7\.com/is/image/Target/[^\"]+', resp.text)
print(f'找到图片: {images[:3]}')

# 如果找到图片，更新数据库
if images:
    image_url = images[0]
    print(f'\n更新数据库: {image_url}')

    conn = sqlite3.connect('faam_products.db')
    cur = conn.cursor()

    # 更新 daily_new_arrivals
    cur.execute('UPDATE daily_new_arrivals SET image_url = ? WHERE tcin = ?', (image_url, tcin))
    print(f'daily_new_arrivals 更新行数: {cur.rowcount}')

    conn.commit()
    conn.close()
    print('更新完成')
