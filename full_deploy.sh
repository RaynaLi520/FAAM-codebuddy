#!/bin/bash
# 完整部署脚本

echo "=== FAAM 完整部署 ==="

# 1. 进入项目目录
cd ~/FAAM

# 2. 拉取最新代码（包括图片和数据库）
echo "1. 拉取最新代码..."
git pull origin main

# 3. 重建数据库
echo "2. 重建数据库..."
python rebuild_db.py

# 4. 检查图片
echo "3. 检查图片..."
if [ -d "static/images/products" ]; then
    echo "   图片数量: $(ls static/images/products/*.jpg 2>/dev/null | wc -l)"
else
    echo "   警告: 图片目录不存在!"
fi

# 5. 重启服务
echo "4. 重启服务..."
pkill -f "python app.py" 2>/dev/null || true
sleep 1
python app.py &
sleep 2

echo "=== 部署完成 ==="
echo "请刷新浏览器访问网站"
