"""
FAAM数据导入脚本
用于将爬虫数据导入到SQLite数据库中
按商品标题+品牌去重（同一商品不同颜色/尺码只保留一条）
"""
import pandas as pd
import sqlite3
import os
import glob
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'faam_products.db')

def parse_price(value):
    """解析价格字符串，移除 $ 符号并转换为浮点数"""
    if pd.isna(value):
        return None
    try:
        price_str = str(value).replace('$', '').replace(',', '').strip()
        return float(price_str) if price_str else None
    except:
        return None

def parse_discount(value):
    """解析折扣字符串，如 '30%' 或 '$5.00' 或 0.3 """
    if pd.isna(value):
        return None
    try:
        val_str = str(value).strip()
        if '%' in val_str:
            return float(val_str.replace('%', '').strip()) / 100
        elif '$' in val_str:
            return parse_price(value)
        else:
            return float(val_str)
    except:
        return None

def parse_int(value):
    """安全解析整数"""
    if pd.isna(value):
        return None
    try:
        val_str = str(value).replace(',', '').strip()
        return int(float(val_str)) if val_str else None
    except:
        return None

def generate_product_id(title, brand):
    """根据标题和品牌生成唯一商品ID"""
    if not title or not brand:
        return None
    normalized = f"{brand.lower().strip()}_{title.lower().strip()}"
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized[:200]

def init_db():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tcin TEXT,
            product_id TEXT UNIQUE,
            title TEXT,
            brand TEXT,
            price REAL,
            retail_price REAL,
            original_price REAL,
            has_promotion TEXT,
            savings_amount TEXT,
            discount_percentage TEXT,
            max_discount REAL,
            is_clearance TEXT,
            material TEXT,
            sales_count INTEGER,
            delivery_date TEXT,
            is_new TEXT,
            rating REAL,
            review_count INTEGER,
            secondary_ratings TEXT,
            color_summary TEXT,
            color TEXT,
            size_summary TEXT,
            bullet_points TEXT,
            image_url TEXT,
            product_url TEXT,
            item_type TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_new_arrivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tcin TEXT,
            title TEXT,
            brand TEXT,
            price REAL,
            image_url TEXT,
            product_url TEXT,
            date_detected DATE,
            is_processed INTEGER DEFAULT 0,
            FOREIGN KEY (tcin) REFERENCES products(tcin)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_brand ON products(brand)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_new ON products(is_new)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_added ON products(date_added)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_id ON products(product_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_item_type ON products(item_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_new_arrivals(date_detected)')

    conn.commit()
    conn.close()
    print("数据库初始化完成")

def import_excel_file(file_path):
    """从Excel文件导入数据，按标题+品牌去重"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return 0

    try:
        print(f"正在读取文件: {file_path}")
        try:
            df = pd.read_excel(file_path, sheet_name=0)
        except:
            try:
                df = pd.read_excel(file_path, sheet_name="商品数据")
            except:
                df = pd.read_excel(file_path, sheet_name="商品详情")

        print(f"共 {len(df)} 行数据")

        # 打印所有列名以便调试
        print(f"Excel列名: {list(df.columns)}")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        imported_count = 0
        skipped_count = 0

        for index, row in df.iterrows():
            try:
                tcin = str(row.get('TCIN', '')).strip()
                title = str(row.get('标题', '')).strip()
                brand = str(row.get('品牌', '')).strip()

                if not tcin or not title:
                    continue

                # 生成商品唯一ID
                product_id = generate_product_id(title, brand)
                if not product_id:
                    continue

                # 检查是否已存在（按 product_id 去重）
                cursor.execute('SELECT id FROM products WHERE product_id = ?', (product_id,))
                if cursor.fetchone():
                    skipped_count += 1
                    continue

                # 解析评论数量
                review_count = parse_int(row.get('评分数量'))

                # 次要评分
                secondary_ratings = str(row.get('分项评分', ''))
                if secondary_ratings == 'nan':
                    secondary_ratings = ''

                # 商品类型
                item_type = str(row.get('商品类型', ''))
                if item_type == 'nan':
                    item_type = ''

                cursor.execute('''
                    INSERT INTO products
                    (tcin, product_id, title, brand, price, retail_price, original_price,
                     has_promotion, savings_amount, discount_percentage, max_discount,
                     is_clearance, material, sales_count, delivery_date, is_new,
                     rating, review_count, secondary_ratings, color_summary, color,
                     size_summary, bullet_points, image_url, product_url, item_type,
                     date_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tcin,
                    product_id,
                    title,
                    brand,
                    parse_price(row.get('价格')),
                    parse_price(row.get('零售价')),
                    parse_price(row.get('原价')),
                    str(row.get('促销活动', '')),
                    str(row.get('节省金额', '')),
                    str(row.get('折扣比例', '')),
                    parse_discount(row.get('最大折扣')),
                    str(row.get('清仓状态', '')),
                    str(row.get('材料(汇总)', '')),
                    parse_int(row.get('购买次数')),
                    str(row.get('预计送达', '')),
                    str(row.get('新品标签', '')),
                    parse_price(row.get('评分')),
                    review_count,
                    secondary_ratings,
                    str(row.get('颜色汇总', '')),
                    str(row.get('颜色', '')),
                    str(row.get('尺码汇总', '')),
                    str(row.get('简洁卖点', '')),
                    str(row.get('图片链接', '')),
                    str(row.get('购买链接', '')),
                    item_type,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                imported_count += 1
            except Exception as e:
                print(f"导入第{index}行时出错: {e}")
                continue

        conn.commit()
        conn.close()

        print(f"成功导入 {imported_count} 条，重复跳过 {skipped_count} 条")
        return imported_count

    except Exception as e:
        print(f"导入文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return 0

def find_and_import_files(data_dir):
    """查找并导入所有Excel文件"""
    if not os.path.exists(data_dir):
        print(f"目录不存在: {data_dir}")
        return

    excel_files = glob.glob(os.path.join(data_dir, "**/*.xlsx"), recursive=True)
    excel_files = [f for f in excel_files if not os.path.basename(f).startswith('~$')]

    if not excel_files:
        print("未找到Excel文件")
        return

    print(f"找到 {len(excel_files)} 个Excel文件")

    total_imported = 0
    for file_path in excel_files:
        print(f"\n处理文件: {os.path.basename(file_path)}")
        count = import_excel_file(file_path)
        total_imported += count

    print(f"\n总计导入 {total_imported} 条记录")

if __name__ == "__main__":
    import sys

    print("="*60)
    print("FAAM 数据导入工具（按商品标题去重）")
    print("="*60)

    init_db()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isfile(path):
            print(f"\n导入单个文件: {path}")
            import_excel_file(path)
        else:
            print(f"\n导入目录: {path}")
            find_and_import_files(path)
    else:
        print("\n查找当前目录下的Excel文件...")
        find_and_import_files(os.getcwd())

    print("\n导入完成!")
