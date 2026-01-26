# -*- coding: utf-8 -*-
"""
===================================
Session 管理模块
===================================

职责：
1. 管理用户登录 Session
2. 使用 Cookie 存储 Session ID
3. 提供 Session 验证和获取当前用户
"""

import secrets
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta
from http import HTTPStatus

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class SessionManager:
    """Session 管理器"""
    
    def __init__(self):
        # 内存存储 Session（生产环境建议使用 Redis）
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_timeout = timedelta(hours=24)  # Session 24小时过期
    
    def create_session(self, user_id: int, username: str, is_admin: bool = False) -> str:
        """
        创建 Session
        
        Args:
            user_id: 用户ID
            username: 用户名
            is_admin: 是否管理员
            
        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = {
            'user_id': user_id,
            'username': username,
            'is_admin': is_admin,
            'created_at': datetime.now(),
            'last_access': datetime.now()
        }
        logger.info(f"[SessionManager] 创建 Session: {username} (session_id={session_id[:8]}...)")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Session 信息
        
        Args:
            session_id: Session ID
            
        Returns:
            Session 信息，如果不存在或已过期返回 None
        """
        if not session_id or session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        # 检查是否过期
        if datetime.now() - session['last_access'] > self._session_timeout:
            logger.info(f"[SessionManager] Session 已过期: {session_id[:8]}...")
            del self._sessions[session_id]
            return None
        
        # 更新最后访问时间
        session['last_access'] = datetime.now()
        return session
    
    def delete_session(self, session_id: str) -> None:
        """删除 Session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"[SessionManager] 删除 Session: {session_id[:8]}...")
    
    def get_session_from_request(self, request_handler: 'BaseHTTPRequestHandler') -> Optional[Dict[str, Any]]:
        """
        从请求中获取 Session
        
        Args:
            request_handler: HTTP 请求处理器
            
        Returns:
            Session 信息，如果不存在返回 None
        """
        # 从 Cookie 中获取 Session ID
        cookie_header = request_handler.headers.get('Cookie', '')
        session_id = self._parse_cookie(cookie_header, 'session_id')
        
        if not session_id:
            return None
        
        return self.get_session(session_id)
    
    def set_session_cookie(self, request_handler: 'BaseHTTPRequestHandler', session_id: str) -> None:
        """
        设置 Session Cookie
        
        Args:
            request_handler: HTTP 请求处理器
            session_id: Session ID
        """
        # 设置 Cookie（HttpOnly, Secure, SameSite）
        cookie = f"session_id={session_id}; Path=/; HttpOnly; Max-Age=86400"  # 24小时
        request_handler.send_header('Set-Cookie', cookie)
    
    def clear_session_cookie(self, request_handler: 'BaseHTTPRequestHandler') -> None:
        """清除 Session Cookie"""
        cookie = "session_id=; Path=/; HttpOnly; Max-Age=0"
        request_handler.send_header('Set-Cookie', cookie)
    
    @staticmethod
    def _parse_cookie(cookie_header: str, key: str) -> Optional[str]:
        """解析 Cookie 字符串"""
        if not cookie_header:
            return None
        
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if cookie.startswith(f'{key}='):
                return cookie[len(key) + 1:]
        return None


# 全局 Session 管理器实例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取 Session 管理器实例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
