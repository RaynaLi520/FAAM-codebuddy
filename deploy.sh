#!/bin/bash
# 完整部署脚本 - 在 Cloud Studio 执行

echo "=== 1. 停止现有服务 ==="
pkill -f "python app.py" 2>/dev/null || true
sleep 1

echo "=== 2. 拉取最新代码 ==="
cd ~/FAAM || cd /workspace/FAAM || cd $(dirname $(find ~ -name "FAAM" -type d 2>/dev/null | head -1))
git pull origin main

echo "=== 3. 导入数据库 ==="
if [ -f "database_data.sql" ]; then
    sqlite3 faam_products.db < database_data.sql
    echo "数据库导入完成"
else
    echo "警告: database_data.sql 不存在"
fi

echo "=== 4. 验证图片数量 ==="
if [ -d "static/images/products" ]; then
    IMAGE_COUNT=$(find static/images/products -type f | wc -l)
    echo "本地图片数量: $IMAGE_COUNT"
else
    echo "警告: static/images/products 目录不存在"
fi

echo "=== 5. 重启服务 ==="
nohup python app.py > app.log 2>&1 &
sleep 3

echo "=== 部署完成 ==="
echo "请访问: http://localhost:5000"
