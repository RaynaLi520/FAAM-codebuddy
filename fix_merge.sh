#!/bin/bash
# 修复 Git 合并冲突

cd ~/FAAM

# 完成合并
git commit -m "Merge from origin/main" --no-edit

# 拉取最新代码
git pull origin main

# 重建数据库
python3 rebuild_db_v3.py

# 检查图片数量
echo "本地图片数量:"
ls static/images/products/*.jpg 2>/dev/null | wc -l

# 重启服务
pkill -f "python app.py" 2>/dev/null
python3 app.py
