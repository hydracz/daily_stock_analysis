# -*- coding: utf-8 -*-
"""
===================================
Web 认证模块
===================================

职责：
1. 实现多用户 Session 认证
2. 支持 Basic Auth 登录（兼容旧版本）
3. 验证用户凭据
4. 提供认证装饰器和工具函数
"""

from __future__ import annotations

import base64
import logging
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING
from http import HTTPStatus

from src.config import get_config
from src.user_service import get_user_service
from web.session import get_session_manager

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class WebAuth:
    """Web 认证管理器（支持多用户）"""
    
    def __init__(self):
        self.config = get_config()
        self.user_service = get_user_service()
        self.session_manager = get_session_manager()
        # 兼容旧版本：如果配置了单用户认证，也启用
        self._legacy_enabled = self._is_legacy_auth_enabled()
        self._legacy_username = self.config.webui_username
        self._legacy_password = self.config.webui_password
    
    def _is_legacy_auth_enabled(self) -> bool:
        """检查是否启用旧版本单用户认证（向后兼容）"""
        username = self.config.webui_username
        password = self.config.webui_password
        return bool(username and password)
    
    @property
    def enabled(self) -> bool:
        """是否启用认证（多用户或单用户）"""
        # 检查是否有用户（多用户模式）
        users = self.user_service.list_users(include_disabled=True)
        if users:
            return True
        # 检查是否配置了单用户认证（向后兼容）
        return self._legacy_enabled
    
    def verify_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        验证用户凭据（多用户模式）
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户信息字典，如果验证失败返回 None
        """
        # 优先使用多用户模式
        user = self.user_service.verify_user(username, password)
        if user:
            return {
                'user_id': user.id,
                'username': user.username,
                'is_admin': user.is_admin
            }
        
        # 向后兼容：检查单用户认证
        if self._legacy_enabled:
            if username == self._legacy_username and password == self._legacy_password:
                return {
                    'user_id': 0,  # 单用户模式使用 0 作为 ID
                    'username': username,
                    'is_admin': True
                }
        
        return None
    
    def parse_basic_auth(self, auth_header: str) -> Optional[Tuple[str, str]]:
        """
        解析 Basic Auth 请求头
        
        Args:
            auth_header: Authorization 请求头值（如 "Basic dXNlcm5hbWU6cGFzc3dvcmQ="）
            
        Returns:
            (username, password) 元组，如果解析失败返回 None
        """
        if not auth_header or not auth_header.startswith('Basic '):
            return None
        
        try:
            # 移除 "Basic " 前缀
            encoded = auth_header[6:]
            # Base64 解码
            decoded = base64.b64decode(encoded).decode('utf-8')
            # 分割用户名和密码
            username, password = decoded.split(':', 1)
            return (username, password)
        except Exception as e:
            logger.warning(f"[WebAuth] 解析 Basic Auth 失败: {e}")
            return None
    
    def check_auth(self, request_handler: 'BaseHTTPRequestHandler') -> Optional[Dict[str, Any]]:
        """
        检查请求是否通过认证（支持 Session 和 Basic Auth）
        
        Args:
            request_handler: HTTP 请求处理器
            
        Returns:
            用户信息字典，如果未通过认证返回 None
        """
        if not self.enabled:
            return {'user_id': 0, 'username': 'guest', 'is_admin': False}  # 未启用认证时，返回访客
        
        # 1. 优先检查 Session（多用户模式）
        session = self.session_manager.get_session_from_request(request_handler)
        if session:
            return {
                'user_id': session['user_id'],
                'username': session['username'],
                'is_admin': session['is_admin']
            }
        
        # 2. 检查 Basic Auth（向后兼容）
        auth_header = request_handler.headers.get('Authorization', '')
        credentials = self.parse_basic_auth(auth_header)
        
        if credentials:
            username, password = credentials
            user_info = self.verify_credentials(username, password)
            if user_info:
                # 创建 Session
                session_id = self.session_manager.create_session(
                    user_id=user_info['user_id'],
                    username=user_info['username'],
                    is_admin=user_info['is_admin']
                )
                self.session_manager.set_session_cookie(request_handler, session_id)
                return user_info
        
        return None
    
    def login(self, request_handler: 'BaseHTTPRequestHandler', username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        用户登录
        
        Args:
            request_handler: HTTP 请求处理器
            username: 用户名
            password: 密码
            
        Returns:
            用户信息字典，如果登录失败返回 None
        """
        user_info = self.verify_credentials(username, password)
        if user_info:
            # 创建 Session
            session_id = self.session_manager.create_session(
                user_id=user_info['user_id'],
                username=user_info['username'],
                is_admin=user_info['is_admin']
            )
            self.session_manager.set_session_cookie(request_handler, session_id)
            return user_info
        return None
    
    def logout(self, request_handler: 'BaseHTTPRequestHandler') -> None:
        """用户登出"""
        session = self.session_manager.get_session_from_request(request_handler)
        if session:
            # 从 Cookie 中获取 Session ID
            cookie_header = request_handler.headers.get('Cookie', '')
            session_id = self.session_manager._parse_cookie(cookie_header, 'session_id')
            if session_id:
                self.session_manager.delete_session(session_id)
        self.session_manager.clear_session_cookie(request_handler)
    
    def send_auth_required(self, request_handler: 'BaseHTTPRequestHandler', redirect_to_login: bool = False) -> None:
        """
        发送 401 Unauthorized 响应，要求客户端提供认证
        
        Args:
            request_handler: HTTP 请求处理器
            redirect_to_login: 是否重定向到登录页面（多用户模式）
        """
        if redirect_to_login:
            # 多用户模式：重定向到登录页面
            request_handler.send_response(HTTPStatus.FOUND)
            request_handler.send_header('Location', '/login')
            request_handler.send_header('Content-Type', 'text/html; charset=utf-8')
            request_handler.end_headers()
            return
        
        # 单用户模式或 Basic Auth：返回 401
        request_handler.send_response(HTTPStatus.UNAUTHORIZED)
        request_handler.send_header('WWW-Authenticate', 'Basic realm="Stock Analysis WebUI"')
        request_handler.send_header('Content-Type', 'text/html; charset=utf-8')
        request_handler.end_headers()
        
        error_body = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>401 Unauthorized</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #d32f2f; }
    </style>
</head>
<body>
    <h1>401 Unauthorized</h1>
    <p>需要认证才能访问此页面。</p>
    <p>请<a href="/login">登录</a>或使用 Basic Auth 认证。</p>
</body>
</html>
"""
        request_handler.wfile.write(error_body.encode('utf-8'))


# 全局认证管理器实例
_auth_manager: Optional[WebAuth] = None


def get_auth_manager() -> WebAuth:
    """获取认证管理器实例"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = WebAuth()
    return _auth_manager


def require_auth(handler_func):
    """
    认证装饰器
    
    用法：
        @require_auth
        def handle_request(query):
            ...
    """
    def wrapper(query_or_form, request_handler=None):
        # 如果未启用认证，直接执行
        auth_manager = get_auth_manager()
        if not auth_manager.enabled:
            return handler_func(query_or_form)
        
        # 如果启用了认证，需要 request_handler 参数
        if request_handler is None:
            # 尝试从 query_or_form 中获取（如果是路由调用）
            # 这种情况下需要特殊处理
            logger.warning("[WebAuth] 装饰器需要 request_handler 参数，但未提供")
            from web.handlers import JsonResponse
            return JsonResponse(
                {"error": "Authentication required"},
                status=HTTPStatus.UNAUTHORIZED
            )
        
        # 检查认证
        if not auth_manager.check_auth(request_handler):
            auth_manager.send_auth_required(request_handler)
            return None  # 已发送响应，返回 None 表示不需要继续处理
        
        # 认证通过，执行原函数
        return handler_func(query_or_form)
    
    return wrapper
