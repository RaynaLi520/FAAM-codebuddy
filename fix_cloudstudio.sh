#!/bin/bash
# Cloud Studio 修复脚本

cd ~/FAAM

echo "=== 修复 Git 冲突 ==="
git config pull.rebase false
git stash
git pull origin main

echo ""
echo "=== 检查数据库 ==="
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('faam_products.db')
    count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    print(f'数据库商品数量: {count}')
    if count < 100:
        print('数据库为空，需要重建!')
        exit(1)
    else:
        print('数据库正常')
        exit(0)
except Exception as e:
    print(f'数据库错误: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "=== 重建数据库 ==="
    rm -f faam_products.db
    python3 rebuild_db.py
fi

echo ""
echo "=== 重启服务 ==="
pkill -f "python app.py" 2>/dev/null
sleep 2
python3 app.py &

echo ""
echo "=== 完成 ==="
echo "等待服务启动..."
sleep 3
echo "服务已启动"
