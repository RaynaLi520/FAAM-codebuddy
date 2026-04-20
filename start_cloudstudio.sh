#!/bin/bash
# Cloud Studio 启动脚本

# 安装依赖
pip install -r requirements.txt

# 启动 Gunicorn
# - workers: 工作进程数
# - bind: 监听端口
# - app: 应用入口
gunicorn --workers 2 --bind 0.0.0.0:8000 app:app
