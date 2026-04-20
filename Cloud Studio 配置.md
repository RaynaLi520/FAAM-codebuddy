# Cloud Studio 部署配置

## 启动命令
```
gunicorn --bind 0.0.0.0:$PORT app:app --workers 2 --timeout 120
```

## 环境变量
- `PORT`: Cloud Studio 自动分配的端口（通常为 8080 或类似）

## 注意事项
1. 数据库文件 `faam_products.db` 需要上传（或新建）
2. 图片文件夹 `images/` 如果为空可以不上传
3. 首次访问会自动创建数据库表
