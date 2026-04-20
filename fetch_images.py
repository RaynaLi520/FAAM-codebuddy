"""
根据 TCIN 从 Target API 获取完整图片URL
用于更新本地Excel中缺少的图片数据
"""
import requests
import json
import time
import random
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Target API 配置
API_KEY = "9f36aeafbe60771e321a7cc95a78140772ab3e96"
TARGET_STORE_ID = "1121"
TARGET_ZIP_CODE = "95628"

VISITOR_ID = ''.join(random.choices('0123456789ABCDEF', k=32))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.target.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_product_detail(tcin):
    """
    调用 Target PDP API 获取商品详情，包括图片URL
    使用原始爬虫的API格式
    """
    detail_url = (
        f"https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
        f"?key={API_KEY}&tcin={tcin}&is_bot=false"
        f"&store_id={TARGET_STORE_ID}"
        f"&pricing_store_id={TARGET_STORE_ID}&has_pricing_store_id=true"
        f"&zip={TARGET_ZIP_CODE}"
        f"&has_financing_options=true&include_obsolete=true"
        f"&visitor_id={VISITOR_ID}&skip_personalized=true"
        f"&skip_variation_hierarchy=true&channel=WEB&page=%2Fp%2FA-{tcin}"
    )
    
    try:
        resp = requests.get(detail_url, headers=HEADERS, timeout=20, verify=False)
        print(f"  状态码: {resp.status_code}")
        
        if resp.status_code != 200:
            return None
        
        json_data = resp.json()
        pdp_data = json_data.get("data", {}).get("product", {})
        
        if not pdp_data:
            print(f"  无PDP数据")
            return None
        
        # 获取图片URL
        item = pdp_data.get("item", {})
        enrichment = item.get("enrichment", {})
        
        # 方式1: primary_image_url
        primary_url = enrichment.get("images", {}).get("primary_image_url")
        
        # 方式2: 从image_info获取
        if not primary_url:
            image_info = enrichment.get("images", {}).get("image_info", {})
            primary = image_info.get("primary_image", {})
            primary_url = primary.get("url")
        
        return {
            'tcin': tcin,
            'primary_image_url': primary_url,
            'title': item.get("product_description", {}).get("title"),
        }
        
    except Exception as e:
        print(f"  错误: {e}")
        return None

def update_database_images():
    """
    更新数据库中的图片URL
    """
    import sqlite3
    
    DB_PATH = 'D:/CodeBuddy/FAAM/faam_products.db'
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有缺少正确图片的 TCIN
    cursor.execute("""
        SELECT tcin, image_url FROM daily_new_arrivals 
        WHERE image_url IS NULL OR image_url = '' OR image_url NOT LIKE '%target.scene7.com%'
        LIMIT 10
    """)
    rows = cursor.fetchall()
    print(f"找到 {len(rows)} 个需要更新图片的TCIN")
    
    updated = 0
    for row in rows:
        tcin, current_url = row
        print(f"\n获取 TCIN {tcin} 的图片...")
        result = get_product_detail(tcin)
        
        if result and result.get('primary_image_url'):
            image_url = result['primary_image_url']
            # 确保URL有正确的参数
            if '?' not in image_url:
                image_url += '?wid=600&hei=600&fmt=jpeg&qlt=80'
            
            cursor.execute("""
                UPDATE daily_new_arrivals 
                SET image_url = ? 
                WHERE tcin = ?
            """, (image_url, tcin))
            
            updated += 1
            print(f"  ✓ 更新成功")
        else:
            print(f"  ✗ 未获取到图片URL")
        
        time.sleep(0.5)
    
    conn.commit()
    conn.close()
    
    print(f"\n更新完成: {updated} 条记录")
    return updated

if __name__ == '__main__':
    print("="*50)
    print("从 Target API 获取图片URL")
    print("="*50)
    
    # 测试几个TCIN
    test_tcins = ['95181561', '1008863107', '95181500']
    
    print("\n测试获取图片:")
    for tcin in test_tcins:
        print(f"\n获取 TCIN: {tcin}")
        result = get_product_detail(tcin)
        if result:
            print(f"  图片URL: {result.get('primary_image_url', 'N/A')}")
        else:
            print(f"  获取失败")
        time.sleep(1)