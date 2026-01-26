# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 数据模型
===================================

定义用户和用户股票列表的数据模型
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.storage import Base


class User(Base):
    """
    用户模型
    
    存储用户账号信息
    """
    __tablename__ = 'users'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户名（唯一）
    username = Column(String(50), nullable=False, unique=True, index=True)
    
    # 密码哈希（使用 bcrypt 加密）
    password_hash = Column(String(255), nullable=False)
    
    # 是否启用
    enabled = Column(Boolean, default=True, nullable=False)
    
    # 是否管理员
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # 关联关系
    stock_lists = relationship("UserStockList", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username={self.username}, enabled={self.enabled}, is_admin={self.is_admin})>"
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'enabled': self.enabled,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_password:
            data['password_hash'] = self.password_hash
        return data


class UserStockList(Base):
    """
    用户股票列表模型
    
    每个用户可以有自己的股票列表
    """
    __tablename__ = 'user_stock_lists'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户ID（外键）
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 股票列表（逗号分隔的股票代码）
    stock_list = Column(Text, nullable=False, default='')
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="stock_lists")
    
    def __repr__(self):
        return f"<UserStockList(user_id={self.user_id}, stock_list={self.stock_list[:50]}...)>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stock_list': self.stock_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
