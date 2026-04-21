#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从本地 Excel 文件导入历史新品数据到数据库
按照 Excel 中的 Launch date 记录每日新品
Brand 映射: WF -> Wild Fable, AND -> A New Day
"""

import sqlite3
import pandas as pd
from datetime import datetime


# ==================== 配置 ====================
DB_PATH = 'faam_products.db'
EXCEL_PATH = 'C:/Users/31837/Desktop/DATA/New_Launched_0311-today(1).xlsx'

# Brand 映射
BRAND_MAPPING = {
    'WF': 'Wild Fable',
    'AND': 'A New Day'
}


def get_db_connection():
    """创建数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_tables(conn):
    """初始化数据库表"""
    cursor = conn.cursor()

    # Daily New Arrivals 表
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

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_new_arrivals(date_detected)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_tcin ON daily_new_arrivals(tcin)')

    conn.commit()


def import_from_excel():
    """
    从 Excel 导入每日新品数据到数据库
    使用数据库中已有的 products 图片 URL
    """
    print(f"\n=== 开始导入 Excel 文件 ===")
    print(f"Excel 路径: {EXCEL_PATH}")

    # 读取 Excel
    df = pd.read_excel(EXCEL_PATH)
    print(f"Excel 总行数: {len(df)}")

    # 检查必要的列
    required_cols = ['TCIN', 'Launch date', 'Brand']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"缺少必要的列: {col}")

    # 连接数据库
    conn = get_db_connection()
    init_tables(conn)
    cursor = conn.cursor()

    # 统计变量
    total_imported = 0
    skipped = 0
    already_exists = 0

    # 按日期分组统计
    date_stats = {}

    print("\n开始导入数据...")

    for idx, row in df.iterrows():
        try:
            # 获取 TCIN
            tcin = str(row['TCIN']).strip()
            if not tcin or tcin == 'nan':
                skipped += 1
                continue

            # 解析 Launch date
            launch_date = pd.to_datetime(row['Launch date'])
            date_str = launch_date.strftime('%Y-%m-%d')

            # 统计
            if date_str not in date_stats:
                date_stats[date_str] = {'total': 0, 'new': 0}
            date_stats[date_str]['total'] += 1

            # 获取品牌
            brand_abbr = str(row['Brand']).strip().upper()
            brand = BRAND_MAPPING.get(brand_abbr, brand_abbr)

            # 获取标题
            title = ''
            if '标题' in df.columns:
                title = str(row['标题']) if pd.notna(row.get('标题')) else ''
            if title == 'nan':
                title = ''

            # 获取价格
            price = None
            if '价格' in df.columns and pd.notna(row.get('价格')):
                try:
                    price = float(row['价格'])
                except:
                    price = None

            # 获取购买链接
            purchase_link = f"https://www.target.com/p/-/{tcin}"
            if '购买链接' in df.columns:
                link = str(row['购买链接']) if pd.notna(row.get('购买链接')) else ''
                if link and '点击' not in link:
                    purchase_link = link

            # 从 products 表获取图片 URL
            cursor.execute('SELECT image_url FROM products WHERE tcin = ?', (tcin,))
            result = cursor.fetchone()
            image_url = None
            if result and result['image_url']:
                image_url = result['image_url']

            # 如果 products 表中没有图片，使用默认 URL
            if not image_url:
                image_url = f"https://target.scene7.com/is/image/Target/{tcin}"

            # 检查是否已存在
            cursor.execute('''
                SELECT id FROM daily_new_arrivals WHERE tcin = ? AND date_detected = ?
            ''', (tcin, date_str))
            if cursor.fetchone():
                already_exists += 1
                skipped += 1
                continue

            # 插入 daily_new_arrivals 表
            cursor.execute('''
                INSERT INTO daily_new_arrivals
                (tcin, title, brand, price, image_url, product_url, date_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (tcin, title, brand, price, image_url, purchase_link, date_str))

            total_imported += 1
            date_stats[date_str]['new'] += 1

        except Exception as e:
            print(f"  [Error] Row {idx}: {e}")
            skipped += 1
            continue

        # 每 20 行显示进度
        if (idx + 1) % 20 == 0:
            conn.commit()
            print(f"  已导入: {total_imported} / {len(df)}")

    # 最终提交
    conn.commit()

    # 关闭连接
    conn.close()

    # 打印统计
    print("\n" + "=" * 60)
    print("导入完成!")
    print(f"  本次新增导入: {total_imported} 条")
    print(f"  已存在跳过: {already_exists} 条")
    print(f"  错误跳过: {skipped} 条")
    print("\n每日新品统计:")
    print("-" * 40)
    for date in sorted(date_stats.keys()):
        stats = date_stats[date]
        print(f"  {date}: {stats['total']} 个 (新增: {stats['new']})")
    print("-" * 40)
    print(f"  总计: {sum(s['total'] for s in date_stats.values())} 个")
    print("=" * 60)

    return total_imported


def show_summary():
    """显示每日新品汇总"""
    print("\n=== 每日新品汇总 ===")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 按日期统计
    cursor.execute('''
        SELECT date_detected, COUNT(*) as count, GROUP_CONCAT(DISTINCT brand) as brands
        FROM daily_new_arrivals
        GROUP BY date_detected
        ORDER BY date_detected DESC
    ''')
    rows = cursor.fetchall()

    print(f"{'日期':<15} {'数量':>6} {'品牌分布':<20}")
    print("-" * 45)
    for row in rows:
        brands = row['brands'] if row['brands'] else ''
        print(f"{row['date_detected']:<15} {row['count']:>6} {brands:<20}")

    # 总计
    cursor.execute('SELECT COUNT(*) FROM daily_new_arrivals')
    total = cursor.fetchone()[0]
    print("-" * 45)
    print(f"{'总计':<15} {total:>6}")

    conn.close()


def main():
    """主函数"""
    print("=" * 60)
    print("Target 历史新品数据导入工具")
    print("=" * 60)

    # 导入数据
    import_from_excel()

    # 显示汇总
    show_summary()

    print("\n" + "=" * 60)
    print("所有任务完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
