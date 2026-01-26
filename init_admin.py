#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================
初始化管理员账户脚本
===================================

用于创建或更新管理员账户

使用方法:
    python init_admin.py <username> <password> [--force]
    
示例:
    python init_admin.py admin mypassword123          # 创建或更新用户（交互式）
    python init_admin.py admin mypassword123 --force # 强制更新密码（非交互式）
    
功能:
    - 如果用户不存在，创建新的管理员账户
    - 如果用户已存在，可以选择更新密码
    - 使用 --force 参数可在非交互式环境中自动更新密码
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.storage import DatabaseManager, get_db
from src.user_service import get_user_service


def main():
    if len(sys.argv) < 3:
        print("用法: python init_admin.py <username> <password> [--force]")
        print("示例: python init_admin.py admin mypassword123")
        print("      python init_admin.py admin mypassword123 --force  # 非交互式模式")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    force_update = '--force' in sys.argv
    
    # 初始化数据库
    db = get_db()
    
    # 获取用户服务
    user_service = get_user_service()
    
    # 检查用户是否已存在
    existing_user = user_service.get_user(username=username)
    
    if existing_user:
        print(f"⚠️  用户 '{username}' 已存在")
        print(f"   用户ID: {existing_user.id}")
        print(f"   管理员: {'是' if existing_user.is_admin else '否'}")
        print(f"   状态: {'启用' if existing_user.enabled else '禁用'}")
        
        if force_update:
            should_update = True
            print(f"\n[--force 模式] 将更新用户密码...")
        else:
            try:
                response = input(f"\n是否要更新此用户的密码? (y/N): ")
                should_update = response.lower() == 'y'
            except EOFError:
                # 非交互式环境，默认不更新
                print(f"\n[非交互式环境] 如需更新密码，请使用 --force 参数")
                should_update = False
        
        if should_update:
            # 更新密码
            print(f"正在更新用户密码...")
            success = user_service.update_user(
                user_id=existing_user.id,
                password=password,
                is_admin=True,  # 确保是管理员
                enabled=True    # 确保已启用
            )
            
            if success:
                print(f"✅ 用户密码更新成功!")
                print(f"   用户名: {existing_user.username}")
                print(f"   用户ID: {existing_user.id}")
                print(f"   管理员: 是")
                print(f"\n现在可以使用此账户登录 WebUI:")
                print(f"   访问: http://localhost:8000/login")
                print(f"   用户名: {existing_user.username}")
            else:
                print(f"❌ 更新失败")
                sys.exit(1)
        else:
            print("已取消")
            sys.exit(0)
    else:
        # 创建新用户
        print(f"正在创建管理员账户: {username}...")
        user = user_service.create_user(
            username=username,
            password=password,
            is_admin=True,
            enabled=True
        )
        
        if user:
            print(f"✅ 管理员账户创建成功!")
            print(f"   用户名: {user.username}")
            print(f"   用户ID: {user.id}")
            print(f"   管理员: {'是' if user.is_admin else '否'}")
            print(f"\n现在可以使用此账户登录 WebUI:")
            print(f"   访问: http://localhost:8000/login")
            print(f"   用户名: {user.username}")
        else:
            print(f"❌ 创建失败: 未知错误")
            sys.exit(1)


if __name__ == "__main__":
    main()
