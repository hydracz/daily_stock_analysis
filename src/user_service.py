# -*- coding: utf-8 -*-
"""
===================================
用户管理服务
===================================

职责：
1. 用户账号管理（增删改查）
2. 密码加密和验证
3. 用户股票列表管理
"""

import logging
import hashlib
import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.storage import DatabaseManager, get_db
from src.models import User, UserStockList

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务"""
    
    def __init__(self):
        self.db = get_db()
    
    # ==================== 密码加密 ====================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用 SHA256 + Salt 加密密码
        
        注意：生产环境建议使用 bcrypt，这里使用简单方案便于部署
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = password_hash.split(':', 1)
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == stored_hash
        except Exception as e:
            logger.error(f"[UserService] 密码验证失败: {e}")
            return False
    
    # ==================== 用户管理 ====================
    
    def create_user(
        self,
        username: str,
        password: str,
        is_admin: bool = False,
        enabled: bool = True
    ) -> Optional[User]:
        """
        创建用户
        
        Args:
            username: 用户名
            password: 密码（明文）
            is_admin: 是否管理员
            enabled: 是否启用
            
        Returns:
            创建的用户对象，如果失败返回 None
        """
        with self.db.get_session() as session:
            # 检查用户名是否已存在
            existing = session.execute(
                select(User).where(User.username == username)
            ).scalar_one_or_none()
            
            if existing:
                logger.warning(f"[UserService] 用户名已存在: {username}")
                return None
            
            # 创建新用户
            password_hash = self.hash_password(password)
            user = User(
                username=username,
                password_hash=password_hash,
                is_admin=is_admin,
                enabled=enabled
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            logger.info(f"[UserService] 创建用户成功: {username}")
            return user
    
    def get_user(self, user_id: Optional[int] = None, username: Optional[str] = None) -> Optional[User]:
        """
        获取用户
        
        Args:
            user_id: 用户ID
            username: 用户名
            
        Returns:
            用户对象，如果不存在返回 None
        """
        with self.db.get_session() as session:
            if user_id:
                return session.execute(
                    select(User).where(User.id == user_id)
                ).scalar_one_or_none()
            elif username:
                return session.execute(
                    select(User).where(User.username == username)
                ).scalar_one_or_none()
            return None
    
    def list_users(self, include_disabled: bool = False) -> List[User]:
        """
        列出所有用户
        
        Args:
            include_disabled: 是否包含已禁用的用户
            
        Returns:
            用户列表
        """
        with self.db.get_session() as session:
            query = select(User)
            if not include_disabled:
                query = query.where(User.enabled == True)
            query = query.order_by(User.created_at.desc())
            return list(session.execute(query).scalars().all())
    
    def update_user(
        self,
        user_id: int,
        password: Optional[str] = None,
        enabled: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        can_custom_task: Optional[bool] = None
    ) -> bool:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            password: 新密码（可选）
            enabled: 是否启用（可选）
            is_admin: 是否管理员（可选）
            can_custom_task: 是否允许自定义任务（可选）
            
        Returns:
            是否更新成功
        """
        with self.db.get_session() as session:
            user = session.execute(
                select(User).where(User.id == user_id)
            ).scalar_one_or_none()
            
            if not user:
                logger.warning(f"[UserService] 用户不存在: {user_id}")
                return False
            
            if password is not None:
                user.password_hash = self.hash_password(password)
            
            if enabled is not None:
                user.enabled = enabled
            
            if is_admin is not None:
                user.is_admin = is_admin
            
            if can_custom_task is not None:
                user.can_custom_task = can_custom_task
            
            user.updated_at = datetime.now()
            session.commit()
            
            logger.info(f"[UserService] 更新用户成功: {user.username}")
            return True
    
    def delete_user(self, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        with self.db.get_session() as session:
            user = session.execute(
                select(User).where(User.id == user_id)
            ).scalar_one_or_none()
            
            if not user:
                logger.warning(f"[UserService] 用户不存在: {user_id}")
                return False
            
            session.delete(user)
            session.commit()
            
            logger.info(f"[UserService] 删除用户成功: {user.username}")
            return True
    
    def verify_user(self, username: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        
        Args:
            username: 用户名
            password: 密码（明文）
            
        Returns:
            用户对象，如果验证失败返回 None
        """
        user = self.get_user(username=username)
        
        if not user:
            logger.warning(f"[UserService] 用户不存在: {username}")
            return None
        
        if not user.enabled:
            logger.warning(f"[UserService] 用户已禁用: {username}")
            return None
        
        if not self.verify_password(password, user.password_hash):
            logger.warning(f"[UserService] 密码错误: {username}")
            return None
        
        return user
    
    # ==================== 用户股票列表管理 ====================
    
    def get_user_stock_list(self, user_id: int) -> str:
        """
        获取用户的股票列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            股票列表字符串（逗号分隔）
        """
        with self.db.get_session() as session:
            stock_list = session.execute(
                select(UserStockList).where(UserStockList.user_id == user_id)
            ).scalar_one_or_none()
            
            if stock_list:
                return stock_list.stock_list
            return ""
    
    def set_user_stock_list(self, user_id: int, stock_list: str) -> bool:
        """
        设置用户的股票列表
        
        Args:
            user_id: 用户ID
            stock_list: 股票列表字符串（逗号分隔）
            
        Returns:
            是否设置成功
        """
        with self.db.get_session() as session:
            # 查找或创建
            user_stock_list = session.execute(
                select(UserStockList).where(UserStockList.user_id == user_id)
            ).scalar_one_or_none()
            
            if user_stock_list:
                user_stock_list.stock_list = stock_list
                user_stock_list.updated_at = datetime.now()
            else:
                user_stock_list = UserStockList(
                    user_id=user_id,
                    stock_list=stock_list
                )
                session.add(user_stock_list)
            
            session.commit()
            logger.info(f"[UserService] 更新用户股票列表成功: user_id={user_id}")
            return True


# 全局服务实例
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """获取用户服务实例"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
