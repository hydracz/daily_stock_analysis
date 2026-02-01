# -*- coding: utf-8 -*-
"""
===================================
Web 路由层 - 请求分发
===================================

职责：
1. 解析请求路径
2. 分发到对应的处理器
3. 支持路由注册和扩展
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Callable, Dict, List, Optional, TYPE_CHECKING, Tuple
from urllib.parse import parse_qs, urlparse

from web.handlers import (
    Response, HtmlResponse, JsonResponse,
    get_page_handler, get_api_handler, get_bot_handler, get_user_handler
)
from web.templates import render_error_page
from web.auth import get_auth_manager
from src.user_service import get_user_service

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


# ============================================================
# 路由定义
# ============================================================

# 路由处理函数类型: (query_params) -> Response
RouteHandler = Callable[[Dict[str, list]], Response]


class Route:
    """路由定义"""
    
    def __init__(
        self,
        path: str,
        method: str,
        handler: RouteHandler,
        description: str = ""
    ):
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.description = description


class Router:
    """
    路由管理器
    
    负责：
    1. 注册路由
    2. 匹配请求路径
    3. 分发到处理器
    """
    
    def __init__(self):
        self._routes: Dict[str, Dict[str, Route]] = {}  # {path: {method: Route}}
    
    def register(
        self,
        path: str,
        method: str,
        handler: RouteHandler,
        description: str = ""
    ) -> None:
        """
        注册路由
        
        Args:
            path: 路由路径
            method: HTTP 方法 (GET, POST, etc.)
            handler: 处理函数
            description: 路由描述
        """
        method = method.upper()
        if path not in self._routes:
            self._routes[path] = {}
        
        self._routes[path][method] = Route(path, method, handler, description)
        logger.debug(f"[Router] 注册路由: {method} {path}")
    
    def get(self, path: str, description: str = "") -> Callable:
        """装饰器：注册 GET 路由"""
        def decorator(handler: RouteHandler) -> RouteHandler:
            self.register(path, "GET", handler, description)
            return handler
        return decorator
    
    def post(self, path: str, description: str = "") -> Callable:
        """装饰器：注册 POST 路由"""
        def decorator(handler: RouteHandler) -> RouteHandler:
            self.register(path, "POST", handler, description)
            return handler
        return decorator
    
    def match(self, path: str, method: str) -> Optional[Route]:
        """
        匹配路由
        
        Args:
            path: 请求路径
            method: HTTP 方法
            
        Returns:
            匹配的路由，或 None
        """
        method = method.upper()
        logger.debug(f"[Router] 匹配路由: {method} {path}")
        logger.debug(f"[Router] 已注册的路由: {list(self._routes.keys())}")
        routes_for_path = self._routes.get(path)
        
        if routes_for_path is None:
            logger.debug(f"[Router] 路径不存在: {path}")
            return None
        
        route = routes_for_path.get(method)
        if route:
            logger.debug(f"[Router] 路由匹配成功: {method} {path}")
        else:
            logger.debug(f"[Router] 路径存在但方法不匹配: {path}, 已注册方法: {list(routes_for_path.keys())}")
        return route
    
    def dispatch(
        self,
        request_handler: 'BaseHTTPRequestHandler',
        method: str
    ) -> None:
        """
        分发请求
        
        Args:
            request_handler: HTTP 请求处理器
            method: HTTP 方法
        """
        # 解析 URL
        parsed = urlparse(request_handler.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # 处理根路径
        if path == "":
            path = "/"
        
        # 健康检查和登录接口不需要认证
        public_paths = ["/health", "/login", "/api/login", "/api/logout"]
        if path in public_paths:
            route = self.match(path, method)
            if route:
                try:
                    # 检查处理器是否需要 request_handler 参数
                    import inspect
                    try:
                        sig = inspect.signature(route.handler)
                        if 'request_handler' in sig.parameters or len(sig.parameters) > 1:
                            response = route.handler(query, request_handler)
                        else:
                            response = route.handler(query)
                    except Exception:
                        # 如果检查失败，尝试直接调用
                        response = route.handler(query)
                    if response:
                        response.send(request_handler)
                    return
                except Exception as e:
                    logger.error(f"[Router] 处理请求失败: {method} {path} - {e}")
                    self._send_error(request_handler, str(e))
                    return
        
        # 检查认证（除了公开路径）
        auth_manager = get_auth_manager()
        if auth_manager.enabled:
            user_info = auth_manager.check_auth(request_handler)
            if not user_info:
                # 接口类路径：返回 401 JSON，避免前端 fetch 收到 302 后解析 HTML 报错
                api_paths_json_401 = {"/analysis", "/task", "/tasks"}
                if path in api_paths_json_401:
                    JsonResponse(
                        {"success": False, "error": "需要登录", "login_url": "/login"},
                        status=HTTPStatus.UNAUTHORIZED,
                    ).send(request_handler)
                    return
                # 多用户模式：重定向到登录页面；单用户模式：使用 Basic Auth
                has_users = len(get_user_service().list_users(include_disabled=True)) > 0
                auth_manager.send_auth_required(request_handler, redirect_to_login=has_users)
                return
        
        # 匹配路由
        route = self.match(path, method)
        
        if route is None:
            # 404 Not Found
            self._send_not_found(request_handler, path)
            return
        
        try:
            # 调用处理器（传递 request_handler 用于获取当前用户）
            # 检查处理器是否需要 request_handler 参数
            import inspect
            try:
                sig = inspect.signature(route.handler)
                if 'request_handler' in sig.parameters or len(sig.parameters) > 1:
                    response = route.handler(query, request_handler)
                else:
                    response = route.handler(query)
            except Exception:
                # 如果检查失败，尝试直接调用
                response = route.handler(query)
            if response:
                response.send(request_handler)
            
        except Exception as e:
            logger.error(f"[Router] 处理请求失败: {method} {path} - {e}")
            self._send_error(request_handler, str(e))
    
    def dispatch_post(
        self,
        request_handler: 'BaseHTTPRequestHandler'
    ) -> None:
        """
        分发 POST 请求（需要读取 body）
        
        Args:
            request_handler: HTTP 请求处理器
        """
        parsed = urlparse(request_handler.path)
        path = parsed.path
        
        # 读取 POST body（保留原始字节用于 Bot Webhook）
        content_length = int(request_handler.headers.get("Content-Length", "0") or "0")
        raw_body_bytes = request_handler.rfile.read(content_length)
        raw_body = raw_body_bytes.decode("utf-8", errors="replace")
        
        # 检查是否是 Bot Webhook 路由
        if path.startswith("/bot/"):
            self._dispatch_bot_webhook(request_handler, path, raw_body_bytes)
            return
        
        # 解析 POST 数据（支持 application/x-www-form-urlencoded、application/json 和 multipart/form-data）
        content_type = request_handler.headers.get("Content-Type", "").lower()
        if "application/json" in content_type:
            # JSON 格式：解析为字典，然后转换为 form_data 格式
            import json
            try:
                json_data = json.loads(raw_body)
                form_data = {k: [str(v)] if not isinstance(v, list) else [str(item) for item in v] 
                            for k, v in json_data.items()}
            except json.JSONDecodeError:
                form_data = {}
        elif "multipart/form-data" in content_type:
            # multipart/form-data 格式：使用 email.message 解析
            try:
                from email import message_from_bytes
                from email.header import decode_header
                msg = message_from_bytes(b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + raw_body_bytes)
                form_data = {}
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_disposition() == 'form-data':
                            name = part.get_param('name', header='content-disposition')
                            if name:
                                value = part.get_payload(decode=True)
                                if value:
                                    form_data.setdefault(name, []).append(value.decode('utf-8', errors='replace'))
            except Exception as e:
                logger.warning(f"[Router] multipart/form-data 解析失败，尝试备用方法: {e}")
                # 备用方法：简单解析（适用于简单表单）
                form_data = {}
                # 尝试从原始 body 中提取字段（简单实现）
                try:
                    import re
                    # 查找 name="field" 后面的内容
                    pattern = r'name="([^"]+)"\r?\n\r?\n([^\r\n]+)'
                    matches = re.findall(pattern, raw_body)
                    for name, value in matches:
                        form_data.setdefault(name, []).append(value)
                except Exception:
                    pass
        else:
            # 表单格式（application/x-www-form-urlencoded）：使用 parse_qs
            form_data = parse_qs(raw_body)
        
        # 公开路径不需要认证
        public_paths = ["/login", "/api/login", "/api/logout"]
        if path in public_paths:
            route = self.match(path, "POST")
            if route:
                logger.debug(f"[Router] 匹配到公开路径: POST {path}")
                try:
                    # 检查处理器是否需要 request_handler 参数
                    import inspect
                    try:
                        sig = inspect.signature(route.handler)
                        logger.debug(f"[Router] 处理器签名: {sig}")
                        if 'request_handler' in sig.parameters or len(sig.parameters) > 1:
                            logger.debug(f"[Router] 调用处理器（带 request_handler）")
                            response = route.handler(form_data, request_handler)
                        else:
                            logger.debug(f"[Router] 调用处理器（不带 request_handler）")
                            response = route.handler(form_data)
                    except Exception as sig_error:
                        logger.warning(f"[Router] 签名检查失败，尝试直接调用: {sig_error}")
                        # 如果检查失败，尝试直接调用
                        response = route.handler(form_data)
                    
                    if response:
                        logger.debug(f"[Router] 准备发送响应: {type(response).__name__}")
                        try:
                            response.send(request_handler)
                            logger.debug(f"[Router] 响应发送成功: POST {path}")
                        except Exception as send_error:
                            logger.error(f"[Router] 发送响应失败: POST {path} - {send_error}", exc_info=True)
                    else:
                        logger.warning(f"[Router] 处理器返回 None: POST {path}")
                    return
                except Exception as e:
                    logger.error(f"[Router] 处理请求失败: POST {path} - {e}", exc_info=True)
                    try:
                        self._send_error(request_handler, str(e))
                    except Exception:
                        pass
                    return
            else:
                logger.warning(f"[Router] 未找到路由: POST {path}")
                self._send_not_found(request_handler, path)
                return
        
        # 检查认证（Bot Webhook 和公开路径除外）
        auth_manager = get_auth_manager()
        if auth_manager.enabled:
            user_info = auth_manager.check_auth(request_handler)
            if not user_info:
                has_users = len(get_user_service().list_users(include_disabled=True)) > 0
                auth_manager.send_auth_required(request_handler, redirect_to_login=has_users)
                return
        
        # 匹配路由
        route = self.match(path, "POST")
        
        if route is None:
            self._send_not_found(request_handler, path)
            return
        
        try:
            # 调用处理器（传递 request_handler 用于获取当前用户）
            import inspect
            try:
                sig = inspect.signature(route.handler)
                if 'request_handler' in sig.parameters or len(sig.parameters) > 1:
                    response = route.handler(form_data, request_handler)
                else:
                    response = route.handler(form_data)
            except Exception:
                # 如果检查失败，尝试直接调用
                response = route.handler(form_data)
            if response:
                response.send(request_handler)
            
        except Exception as e:
            logger.error(f"[Router] 处理 POST 请求失败: {path} - {e}")
            self._send_error(request_handler, str(e))
    
    def _dispatch_bot_webhook(
        self,
        request_handler: 'BaseHTTPRequestHandler',
        path: str,
        body: bytes
    ) -> None:
        """
        分发 Bot Webhook 请求
        
        Bot Webhook 需要原始 body 和 headers，与普通路由处理不同。
        
        Args:
            request_handler: HTTP 请求处理器
            path: 请求路径
            body: 原始请求体字节
        """
        # 提取平台名称：/bot/feishu -> feishu
        parts = path.strip('/').split('/')
        if len(parts) < 2:
            self._send_not_found(request_handler, path)
            return
        
        platform = parts[1]
        
        # 获取请求头
        headers = {key: value for key, value in request_handler.headers.items()}
        
        try:
            bot_handler = get_bot_handler()
            response = bot_handler.handle_webhook(platform, {}, headers, body)
            response.send(request_handler)
            
        except Exception as e:
            logger.error(f"[Router] 处理 Bot Webhook 失败: {path} - {e}")
            self._send_error(request_handler, str(e))
    
    def list_routes(self) -> List[Tuple[str, str, str]]:
        """
        列出所有路由
        
        Returns:
            [(method, path, description), ...]
        """
        routes = []
        for path, methods in self._routes.items():
            for method, route in methods.items():
                routes.append((method, path, route.description))
        return sorted(routes, key=lambda x: (x[1], x[0]))
    
    def _send_not_found(
        self,
        request_handler: 'BaseHTTPRequestHandler',
        path: str
    ) -> None:
        """发送 404 响应"""
        body = render_error_page(404, "页面未找到", f"路径 {path} 不存在")
        response = HtmlResponse(body, status=HTTPStatus.NOT_FOUND)
        response.send(request_handler)
    
    def _send_error(
        self,
        request_handler: 'BaseHTTPRequestHandler',
        message: str
    ) -> None:
        """发送 500 响应"""
        body = render_error_page(500, "服务器内部错误", message)
        response = HtmlResponse(body, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        response.send(request_handler)


# ============================================================
# 默认路由注册
# ============================================================

def create_default_router() -> Router:
    """创建并配置默认路由"""
    router = Router()
    
    # 获取处理器
    page_handler = get_page_handler()
    api_handler = get_api_handler()
    user_handler = get_user_handler()
    
    # === 页面路由 ===
    router.register(
        "/", "GET",
        lambda q, rh: page_handler.handle_index(rh),
        "配置首页"
    )
    
    router.register(
        "/update", "POST",
        lambda form, rh: page_handler.handle_update(form, rh),
        "更新配置"
    )
    
    router.register(
        "/login", "GET",
        lambda q: user_handler.handle_login_page(),
        "登录页面"
    )
    
    router.register(
        "/admin/users", "GET",
        lambda q, rh: user_handler.handle_user_manage(rh),
        "用户管理页面"
    )
    
    # === API 路由 ===
    router.register(
        "/health", "GET",
        lambda q: api_handler.handle_health(),
        "健康检查"
    )
    
    router.register(
        "/analysis", "GET",
        lambda q: api_handler.handle_analysis(q),
        "触发股票分析"
    )
    
    router.register(
        "/tasks", "GET",
        lambda q: api_handler.handle_tasks(q),
        "查询任务列表"
    )
    
    router.register(
        "/task", "GET",
        lambda q: api_handler.handle_task_status(q),
        "查询任务状态"
    )
    
    # === 用户管理 API 路由 ===
    router.register(
        "/api/login", "POST",
        lambda form, rh: user_handler.handle_login(form, rh),
        "用户登录"
    )
    
    router.register(
        "/api/logout", "GET",
        lambda q, rh: user_handler.handle_logout(rh),
        "用户登出"
    )
    
    router.register(
        "/api/admin/users", "POST",
        lambda form, rh: user_handler.handle_create_user(form, rh),
        "创建用户"
    )
    
    router.register(
        "/api/admin/users", "DELETE",
        lambda q, rh: user_handler.handle_delete_user(q, rh),
        "删除用户"
    )
    
    router.register(
        "/api/admin/users", "GET",
        lambda q, rh: user_handler.handle_get_user_detail(q, rh),
        "获取用户详情"
    )
    
    router.register(
        "/api/admin/users/password", "POST",
        lambda form, rh: user_handler.handle_update_user_password(form, rh),
        "修改用户密码（管理员）"
    )
    
    router.register(
        "/api/admin/users/role", "POST",
        lambda form, rh: user_handler.handle_update_user_role(form, rh),
        "修改用户角色"
    )
    
    router.register(
        "/api/admin/users/status", "POST",
        lambda form, rh: user_handler.handle_update_user_status(form, rh),
        "启用/禁用用户"
    )
    
    router.register(
        "/api/users/password", "POST",
        lambda form, rh: user_handler.handle_update_user_password(form, rh),
        "修改自己的密码"
    )
    
    # === Bot Webhook 路由 ===
    # 注意：Bot Webhook 路由在 dispatch_post 中特殊处理
    # 这里只是为了在路由列表中显示
    # 实际请求会被 _dispatch_bot_webhook 方法处理
    
    # 飞书机器人 Webhook
    router.register(
        "/bot/feishu", "POST",
        lambda form: JsonResponse({"error": "Use POST with JSON body"}),
        "飞书机器人 Webhook"
    )
    
    # 钉钉机器人 Webhook
    router.register(
        "/bot/dingtalk", "POST",
        lambda form: JsonResponse({"error": "Use POST with JSON body"}),
        "钉钉机器人 Webhook"
    )
    
    # 企业微信机器人 Webhook（开发中）
    # router.register(
    #     "/bot/wecom", "POST",
    #     lambda form: JsonResponse({"error": "Use POST with JSON body"}),
    #     "企业微信机器人 Webhook"
    # )
    
    # Telegram 机器人 Webhook（开发中）
    # router.register(
    #     "/bot/telegram", "POST",
    #     lambda form: JsonResponse({"error": "Use POST with JSON body"}),
    #     "Telegram 机器人 Webhook"
    # )
    
    return router


# 全局默认路由实例
_default_router: Router | None = None


def get_router() -> Router:
    """获取默认路由实例"""
    global _default_router
    if _default_router is None:
        _default_router = create_default_router()
    return _default_router
