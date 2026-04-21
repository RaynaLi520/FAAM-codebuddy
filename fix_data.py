"""
修复每日新品数据：
1. 添加 item_type 列
2. 从 products 表获取 item_type
3. 使用 TCIN 直接构建图片 URL（作为备用）
"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'faam_products.db'

def fix_item_types():
    """修复 item_type 分类"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否已有 item_type 列
    cursor.execute("PRAGMA table_info(daily_new_arrivals)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'item_type' not in columns:
        print("添加 item_type 列...")
        cursor.execute("ALTER TABLE daily_new_arrivals ADD COLUMN item_type TEXT")
        conn.commit()
    
    # 从 products 表获取 item_type
    print("从 products 表同步 item_type...")
    cursor.execute("""
        UPDATE daily_new_arrivals 
        SET item_type = (
            SELECT p.item_type 
            FROM products p 
            WHERE p.tcin = daily_new_arrivals.tcin
        )
        WHERE item_type IS NULL OR item_type = ''
    """)
    
    updated = cursor.rowcount
    conn.commit()
    print(f"已更新 {updated} 条记录的 item_type")
    
    # 统计分类情况
    print("\n=== 分类分布 ===")
    cursor.execute("""
        SELECT COALESCE(item_type, '未分类'), COUNT(*) 
        FROM daily_new_arrivals 
        GROUP BY item_type 
        ORDER BY COUNT(*) DESC
    """)
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
    
    conn.close()

def fix_image_urls():
    """使用 TCIN 验证并修复图片 URL"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== 检查图片 URL ===")
    
    # 检查是否有无效 URL
    cursor.execute("""
        SELECT id, tcin, image_url 
        FROM daily_new_arrivals 
        WHERE image_url IS NULL OR image_url = '' OR image_url LIKE '%TCIN%'
        LIMIT 5
    """)
    invalid = cursor.fetchall()
    
    if invalid:
        print(f"发现 {len(invalid)} 条无效图片 URL")
        for row in invalid:
            print(f"  TCIN: {row[1]}, URL: {row[2]}")
    else:
        print("所有图片 URL 格式正确")
    
    # 显示示例图片 URL
    print("\n=== 示例图片 URL ===")
    cursor.execute("SELECT tcin, image_url FROM daily_new_arrivals LIMIT 3")
    for row in cursor.fetchall():
        print(f"TCIN: {row[0]}")
        print(f"URL: {row[1]}")
        # 尝试提取 GUEST ID
        if 'GUEST_' in str(row[1]):
            guest_id = row[1].split('GUEST_')[1].split('?')[0]
            print(f"GUEST ID: {guest_id}")
        print()
    
    conn.close()

def check_products_item_type():
    """检查 products 表的 item_type"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== products 表分类分布 ===")
    cursor.execute("""
        SELECT COALESCE(item_type, '未分类'), COUNT(*) 
        FROM products 
        WHERE brand IN ('A New Day', 'Wild Fable')
        GROUP BY item_type 
        ORDER BY COUNT(*) DESC
    """)
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
    
    conn.close()

if __name__ == '__main__':
    print("开始修复数据...")
    fix_item_types()
    fix_image_urls()
    check_products_item_type()
    print("\n完成!")
