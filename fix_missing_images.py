import requests
import re
import sqlite3
import time

def fetch_image_from_target(tcin):
    """从 Target 网站获取产品图片"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        url = f'https://www.target.com/p/-/A-{tcin}'
        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code == 200 and 'scene7.com' in resp.text:
            images = re.findall(r'https://target\.scene7\.com/is/image/Target/[^\?"]+', resp.text)
            if images:
                # 返回完整尺寸的 URL
                return images[0].split('?')[0] + '?wid=800&hei=800&qlt=80&fmt=jpeg'

        # 尝试 Product API
        api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/product_overview?key=ff457966e64f5d6ef5d44da2c6f8dfcc&tcin={tcin}&store=2141'
        resp = requests.get(api_url, headers={'User-Agent': headers['User-Agent'], 'Accept': 'application/json'}, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            # 尝试从 API 响应中提取图片
            if 'data' in data and 'product' in data['data']:
                product = data['data']['product']
                if 'images' in product:
                    for img in product['images']:
                        if img.get('kind') == 'PRIMARY':
                            return img.get('url')
    except Exception as e:
        print(f'  请求错误: {e}')

    return None

def main():
    conn = sqlite3.connect('faam_products.db')
    cur = conn.cursor()

    # 找出所有 image_url 为空的记录
    print('=== 查找所有缺少图片的记录 ===')

    # 检查 daily_new_arrivals
    cur.execute('''
        SELECT tcin, title FROM daily_new_arrivals
        WHERE image_url IS NULL OR image_url = ''
    ''')
    missing_dna = cur.fetchall()
    print(f'daily_new_arrivals 中缺少图片: {len(missing_dna)} 条')

    # 检查 products
    cur.execute('''
        SELECT tcin, title FROM products
        WHERE image_url IS NULL OR image_url = ''
    ''')
    missing_p = cur.fetchall()
    print(f'products 中缺少图片: {len(missing_p)} 条')

    if not missing_dna:
        print('\n所有图片都已完整!')
        conn.close()
        return

    print(f'\n=== 开始补全 {len(missing_dna)} 条记录的图片 ===')

    updated_count = 0
    for tcin, title in missing_dna:
        print(f'\n处理 TCIN: {tcin}')
        print(f'  标题: {title[:50]}...' if len(title) > 50 else f'  标题: {title}')

        # 先从 products 表查找是否有这个 TCIN
        cur.execute('SELECT image_url FROM products WHERE tcin = ?', (tcin,))
        row = cur.fetchone()

        if row and row[0]:
            print(f'  从 products 表获取: {row[0][:60]}...')
            cur.execute('UPDATE daily_new_arrivals SET image_url = ? WHERE tcin = ?', (row[0], tcin))
            updated_count += 1
        else:
            # 从 Target 网站获取
            print('  正在从 Target 网站获取...')
            image_url = fetch_image_from_target(tcin)

            if image_url:
                print(f'  获取成功: {image_url[:60]}...')
                cur.execute('UPDATE daily_new_arrivals SET image_url = ? WHERE tcin = ?', (image_url, tcin))
                updated_count += 1
            else:
                print('  获取失败')

            time.sleep(0.5)  # 避免请求过快

    conn.commit()

    # 验证结果
    print('\n=== 验证结果 ===')
    cur.execute('''
        SELECT COUNT(*) FROM daily_new_arrivals
        WHERE image_url IS NULL OR image_url = ''
    ''')
    remaining = cur.fetchone()[0]
    print(f'剩余缺少图片的记录: {remaining}')
    print(f'本次更新: {updated_count} 条')

    conn.close()

if __name__ == '__main__':
    main()
