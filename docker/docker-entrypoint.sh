#!/bin/bash
# ===================================
# Docker 容器启动入口脚本
# ===================================
# 支持自动初始化管理员账户

set -e

# 如果设置了管理员账户环境变量，则自动初始化
if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "🔧 检测到管理员账户配置，正在初始化..."
    python init_admin.py "$ADMIN_USERNAME" "$ADMIN_PASSWORD" --force || {
        echo "⚠️  管理员账户初始化失败，继续启动..."
    }
fi

# 执行原始命令
exec "$@"
