# -*- coding: utf-8 -*-
"""
===================================
Web 认证模块
===================================

职责：
1. 实现 Basic Auth 认证
2. 验证用户凭据
3. 提供认证装饰器和工具函数
"""

from __future__ import annotations

import base64
import logging
from typing import Optional, Tuple, TYPE_CHECKING
from http import HTTPStatus

from src.config import get_config

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class WebAuth:
    """Web 认证管理器"""
    
    def __init__(self):
        self.config = get_config()
        self._enabled = self._is_auth_enabled()
        self._username = self.config.webui_username
        self._password = self.config.webui_password
    
    def _is_auth_enabled(self) -> bool:
        """检查是否启用认证"""
        username = self.config.webui_username
        password = self.config.webui_password
        # 如果配置了用户名和密码，则启用认证
        return bool(username and password)
    
    @property
    def enabled(self) -> bool:
        """是否启用认证"""
        return self._enabled
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """
        验证用户凭据
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            验证是否通过
        """
        if not self._enabled:
            return True  # 未启用认证时，直接通过
        
        return (
            username == self._username and
            password == self._password
        )
    
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
    
    def check_auth(self, request_handler: 'BaseHTTPRequestHandler') -> bool:
        """
        检查请求是否通过认证
        
        Args:
            request_handler: HTTP 请求处理器
            
        Returns:
            是否通过认证
        """
        if not self._enabled:
            return True  # 未启用认证时，直接通过
        
        auth_header = request_handler.headers.get('Authorization', '')
        credentials = self.parse_basic_auth(auth_header)
        
        if credentials is None:
            return False
        
        username, password = credentials
        return self.verify_credentials(username, password)
    
    def send_auth_required(self, request_handler: 'BaseHTTPRequestHandler') -> None:
        """
        发送 401 Unauthorized 响应，要求客户端提供认证
        
        Args:
            request_handler: HTTP 请求处理器
        """
        request_handler.send_response(HTTPStatus.UNAUTHORIZED)
        request_handler.send_header('WWW-Authenticate', 'Basic realm="Stock Analysis WebUI"')
        request_handler.send_header('Content-Type', 'text/html; charset=utf-8')
        request_handler.end_headers()
        
        error_body = b"""
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
    <p>请在浏览器中输入用户名和密码。</p>
</body>
</html>
"""
        request_handler.wfile.write(error_body)


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
