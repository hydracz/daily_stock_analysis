# -*- coding: utf-8 -*-
"""
===================================
Web 处理器层 - 请求处理
===================================

职责：
1. 处理各类 HTTP 请求
2. 调用服务层执行业务逻辑
3. 返回响应数据

处理器分类：
- PageHandler: 页面请求处理
- ApiHandler: API 接口处理
"""

from __future__ import annotations

import json
import re
import logging
from email.utils import formatdate
from http import HTTPStatus
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

from web.services import get_config_service, get_analysis_service
from web.templates import render_config_page, render_login_page, render_user_manage_page
from src.enums import ReportType
from src.user_service import get_user_service
from web.auth import get_auth_manager

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


# ============================================================
# 响应辅助类
# ============================================================

class Response:
    """HTTP 响应封装"""
    
    def __init__(
        self,
        body: bytes,
        status: HTTPStatus = HTTPStatus.OK,
        content_type: str = "text/html; charset=utf-8"
    ):
        self.body = body
        self.status = status
        self.content_type = content_type
    
    def send(self, handler: 'BaseHTTPRequestHandler') -> None:
        """
        发送响应到客户端
        
        完全绕过 BaseHTTPRequestHandler 的响应发送机制，手动构建并发送 HTTP/1.1 响应。
        这样可以确保使用正确的协议版本，避免 curl 等客户端报 HTTP/0.9 错误。
        """
        try:
            # 确保使用 HTTP/1.1 协议版本
            handler.protocol_version = "HTTP/1.1"
            if hasattr(handler, 'request_version'):
                handler.request_version = "HTTP/1.1"
            
            # 收集通过 send_header 设置的响应头（如 Set-Cookie）
            collected_headers = self._collect_custom_headers(handler)
            
            # 手动构建并发送 HTTP/1.1 响应行
            status_line = f"HTTP/1.1 {self.status.value} {self.status.phrase}\r\n"
            handler.wfile.write(status_line.encode('ascii'))
            
            # 构建并发送所有响应头
            headers = self._build_response_headers(handler, collected_headers)
            handler.wfile.write(''.join(headers).encode('ascii'))
            
            # 发送响应体
            handler.wfile.write(self.body)
            handler.wfile.flush()
            
            logger.debug(f"[Response] 响应已发送: {self.status} {len(self.body)} bytes, Content-Type: {self.content_type}")
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            logger.debug(f"[Response] 客户端已断开连接: {e}")
        except Exception as e:
            logger.error(f"[Response] 发送响应失败: {e}", exc_info=True)
            raise
    
    def _collect_custom_headers(self, handler: 'BaseHTTPRequestHandler') -> list[str]:
        """收集通过 send_header 设置的响应头（如 Set-Cookie）"""
        collected = []
        if hasattr(handler, '_headers_buffer') and handler._headers_buffer:
            for header_line in handler._headers_buffer:
                if isinstance(header_line, tuple) and len(header_line) == 2:
                    collected.append(f"{header_line[0]}: {header_line[1]}\r\n")
                elif isinstance(header_line, bytes):
                    collected.append(header_line.decode('ascii', errors='replace'))
                elif isinstance(header_line, str):
                    collected.append(header_line)
        return collected
    
    def _build_response_headers(self, handler: 'BaseHTTPRequestHandler', custom_headers: list[str]) -> list[str]:
        """构建完整的响应头列表"""
        headers = [
            f"Server: {handler.version_string()}\r\n",
            f"Date: {formatdate(timeval=None, localtime=False, usegmt=True)}\r\n",
            f"Content-Type: {self.content_type}\r\n",
            f"Content-Length: {len(self.body)}\r\n",
        ]
        
        # 添加自定义响应头（如 Set-Cookie）
        headers.extend(custom_headers)
        
        # 添加标准安全响应头
        headers.extend([
            "X-Content-Type-Options: nosniff\r\n",
            "X-Frame-Options: SAMEORIGIN\r\n",
            "X-XSS-Protection: 1; mode=block\r\n",
            "Referrer-Policy: no-referrer-when-downgrade\r\n",
            "Access-Control-Allow-Origin: *\r\n",
            "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n",
            "Access-Control-Allow-Headers: Content-Type, Authorization\r\n",
            "Access-Control-Allow-Credentials: true\r\n",
            "\r\n",  # 空行，分隔响应头和响应体
        ])
        return headers


class JsonResponse(Response):
    """JSON 响应封装"""
    
    def __init__(
        self,
        data: Dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK
    ):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        super().__init__(
            body=body,
            status=status,
            content_type="application/json; charset=utf-8"
        )


class HtmlResponse(Response):
    """HTML 响应封装"""
    
    def __init__(
        self,
        body: bytes,
        status: HTTPStatus = HTTPStatus.OK
    ):
        super().__init__(
            body=body,
            status=status,
            content_type="text/html; charset=utf-8"
        )


class RedirectResponse(Response):
    """重定向响应封装"""
    
    def __init__(self, location: str):
        redirect_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0;url={location}">
    <title>正在跳转...</title>
</head>
<body>
    <p>正在跳转，<a href="{location}">点击这里</a>如果页面没有自动跳转。</p>
</body>
</html>
""".encode('utf-8')
        super().__init__(
            body=redirect_html,
            status=HTTPStatus.FOUND,
            content_type="text/html; charset=utf-8"
        )
        self.location = location
    
    def _build_response_headers(self, handler: 'BaseHTTPRequestHandler', custom_headers: list[str]) -> list[str]:
        """构建完整的响应头列表（包含 Location 头）"""
        headers = [
            f"Server: {handler.version_string()}\r\n",
            f"Date: {formatdate(timeval=None, localtime=False, usegmt=True)}\r\n",
            f"Location: {self.location}\r\n",
            f"Content-Type: {self.content_type}\r\n",
            f"Content-Length: {len(self.body)}\r\n",
        ]
        
        # 添加自定义响应头（如 Set-Cookie）
        headers.extend(custom_headers)
        
        # 添加标准安全响应头
        headers.extend([
            "X-Content-Type-Options: nosniff\r\n",
            "X-Frame-Options: SAMEORIGIN\r\n",
            "X-XSS-Protection: 1; mode=block\r\n",
            "Referrer-Policy: no-referrer-when-downgrade\r\n",
            "\r\n",  # 空行，分隔响应头和响应体
        ])
        return headers


# ============================================================
# 页面处理器
# ============================================================

class PageHandler:
    """页面请求处理器"""
    
    def __init__(self):
        self.config_service = get_config_service()
        self.user_service = get_user_service()
        self.auth_manager = get_auth_manager()
    
    def handle_index(self, request_handler: 'BaseHTTPRequestHandler') -> Response:
        """处理首页请求 GET /"""
        # 获取当前用户
        user_info = self.auth_manager.check_auth(request_handler)
        if not user_info:
            user_info = {'user_id': 0, 'username': 'guest', 'is_admin': False}
        
        # 获取用户的股票列表
        if user_info['user_id'] > 0:
            # 多用户模式：从数据库获取
            stock_list = self.user_service.get_user_stock_list(user_info['user_id'])
        else:
            # 单用户模式或未登录：从 .env 获取
            stock_list = self.config_service.get_stock_list()
        
        env_filename = self.config_service.get_env_filename()
        body = render_config_page(
            stock_list, 
            env_filename, 
            current_user=user_info.get('username', 'guest'),
            is_admin=user_info.get('is_admin', False)
        )
        return HtmlResponse(body)
    
    def handle_update(self, form_data: Dict[str, list], request_handler: 'BaseHTTPRequestHandler') -> Response:
        """
        处理配置更新 POST /update
        
        Args:
            form_data: 表单数据
            request_handler: HTTP 请求处理器（用于获取当前用户）
        """
        # 获取当前用户
        user_info = self.auth_manager.check_auth(request_handler)
        if not user_info:
            return JsonResponse(
                {"success": False, "error": "需要登录"},
                status=HTTPStatus.UNAUTHORIZED
            )
        
        stock_list = form_data.get("stock_list", [""])[0]
        
        if user_info['user_id'] > 0:
            # 多用户模式：保存到数据库
            normalized = self._normalize_stock_list(stock_list)
            self.user_service.set_user_stock_list(user_info['user_id'], normalized)
        else:
            # 单用户模式：保存到 .env
            normalized = self.config_service.set_stock_list(stock_list)
        
        env_filename = self.config_service.get_env_filename()
        body = render_config_page(
            normalized, 
            env_filename, 
            message="已保存",
            current_user=user_info.get('username', 'guest'),
            is_admin=user_info.get('is_admin', False)
        )
        return HtmlResponse(body)
    
    @staticmethod
    def _normalize_stock_list(value: str) -> str:
        """规范化股票列表格式"""
        parts = [p.strip() for p in value.replace("\n", ",").split(",")]
        parts = [p for p in parts if p]
        return ",".join(parts)


# ============================================================
# API 处理器
# ============================================================

class ApiHandler:
    """API 请求处理器"""
    
    def __init__(self):
        self.analysis_service = get_analysis_service()
    
    def handle_health(self) -> Response:
        """
        健康检查 GET /health
        
        返回:
            {
                "status": "ok",
                "timestamp": "2026-01-19T10:30:00",
                "service": "stock-analysis-webui"
            }
        """
        data = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "stock-analysis-webui"
        }
        return JsonResponse(data)
    
    def handle_analysis(self, query: Dict[str, list]) -> Response:
        """
        触发股票分析 GET /analysis?code=xxx
        
        Args:
            query: URL 查询参数
            
        返回:
            {
                "success": true,
                "message": "分析任务已提交",
                "code": "600519",
                "task_id": "600519_20260119_103000"
            }
        """
        # 获取股票代码参数
        code_list = query.get("code", [])
        if not code_list or not code_list[0].strip():
            return JsonResponse(
                {"success": False, "error": "缺少必填参数: code (股票代码)"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        code = code_list[0].strip()

        # 验证股票代码格式：A股(6位数字) / 港股(HK+5位数字) / 美股(1-5个大写字母+.+2个后缀字母)
        code = code.upper()
        is_a_stock = re.match(r'^\d{6}$', code)
        is_hk_stock = re.match(r'^HK\d{5}$', code)
        is_us_stock = re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', code.upper())

        if not (is_a_stock or is_hk_stock or is_us_stock):
            return JsonResponse(
                {"success": False, "error": f"无效的股票代码格式: {code} (A股6位数字 / 港股HK+5位数字 / 美股1-5个字母)"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        # 获取报告类型参数（默认完整报告）
        report_type_str = query.get("report_type", ["full"])[0]
        report_type = ReportType.from_str(report_type_str)
        # 强制刷新：默认关闭，开启后忽略历史缓存并重新拉数、分析、保存
        force_refresh_str = query.get("force_refresh", ["false"])[0]
        force_refresh = str(force_refresh_str).lower() in ("1", "true", "yes")
        
        # 提交异步分析任务
        try:
            result = self.analysis_service.submit_analysis(
                code, report_type=report_type, force_refresh=force_refresh
            )
            return JsonResponse(result)
        except Exception as e:
            logger.error(f"[ApiHandler] 提交分析任务失败: {e}")
            return JsonResponse(
                {"success": False, "error": f"提交任务失败: {str(e)}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    def handle_tasks(self, query: Dict[str, list]) -> Response:
        """
        查询任务列表 GET /tasks
        
        Args:
            query: URL 查询参数 (可选 limit)
            
        返回:
            {
                "success": true,
                "tasks": [...]
            }
        """
        limit_list = query.get("limit", ["20"])
        try:
            limit = int(limit_list[0])
        except ValueError:
            limit = 20
        
        tasks = self.analysis_service.list_tasks(limit=limit)
        return JsonResponse({"success": True, "tasks": tasks})
    
    def handle_task_status(self, query: Dict[str, list]) -> Response:
        """
        查询单个任务状态 GET /task?id=xxx
        
        Args:
            query: URL 查询参数
        """
        task_id_list = query.get("id", [])
        if not task_id_list or not task_id_list[0].strip():
            return JsonResponse(
                {"success": False, "error": "缺少必填参数: id (任务ID)"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        task_id = task_id_list[0].strip()
        task = self.analysis_service.get_task_status(task_id)
        
        if task is None:
            return JsonResponse(
                {"success": False, "error": f"任务不存在: {task_id}"},
                status=HTTPStatus.NOT_FOUND
            )
        
        return JsonResponse({"success": True, "task": task})
    


# ============================================================
# 用户管理处理器
# ============================================================

class UserHandler:
    """用户管理处理器"""
    
    def __init__(self):
        self.user_service = get_user_service()
        self.auth_manager = get_auth_manager()
    
    def _require_admin(self, request_handler: 'BaseHTTPRequestHandler') -> Optional[Dict[str, Any]]:
        """
        检查管理员权限
        
        Returns:
            用户信息字典，如果不是管理员返回 None
        """
        user_info = self.auth_manager.check_auth(request_handler)
        if not user_info or not user_info.get('is_admin'):
            return None
        return user_info
    
    def _parse_user_id(self, query: Dict[str, list], param_name: str = "id") -> tuple[Optional[int], Optional[Response]]:
        """
        解析用户ID参数
        
        Returns:
            (user_id, error_response) 元组，如果解析失败返回 (None, error_response)
        """
        user_id_list = query.get(param_name, [])
        if not user_id_list:
            return None, JsonResponse(
                {"success": False, "error": f"缺少{param_name}参数"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        try:
            user_id = int(user_id_list[0])
            return user_id, None
        except ValueError:
            return None, JsonResponse(
                {"success": False, "error": f"无效的{param_name}"},
                status=HTTPStatus.BAD_REQUEST
            )
    
    def handle_login_page(self) -> Response:
        """显示登录页面 GET /login"""
        body = render_login_page()
        return HtmlResponse(body)
    
    def handle_login(self, form_data: Dict[str, list], request_handler: 'BaseHTTPRequestHandler') -> Response:
        """
        处理登录 POST /api/login
        
        Args:
            form_data: 表单数据
            request_handler: HTTP 请求处理器（用于设置 Cookie）
        """
        try:
            username = form_data.get("username", [""])[0].strip() if form_data.get("username") else ""
            password = form_data.get("password", [""])[0].strip() if form_data.get("password") else ""
            
            logger.debug(f"[UserHandler] 登录请求 - username: {username}, form_data keys: {list(form_data.keys())}")
            
            if not username or not password:
                logger.warning(f"[UserHandler] 登录失败: 用户名或密码为空")
                return JsonResponse(
                    {"success": False, "error": "用户名和密码不能为空"},
                    status=HTTPStatus.BAD_REQUEST
                )
            
            user_info = self.auth_manager.login(request_handler, username, password)
            if user_info:
                logger.info(f"[UserHandler] 登录成功: {username}")
                return JsonResponse({
                    "success": True,
                    "message": "登录成功",
                    "user": {
                        "id": user_info['user_id'],
                        "username": user_info['username'],
                        "is_admin": user_info['is_admin']
                    }
                })
            else:
                logger.warning(f"[UserHandler] 登录失败: 用户名或密码错误 - {username}")
                return JsonResponse(
                    {"success": False, "error": "用户名或密码错误"},
                    status=HTTPStatus.UNAUTHORIZED
                )
        except Exception as e:
            logger.error(f"[UserHandler] 登录处理异常: {e}", exc_info=True)
            return JsonResponse(
                {"success": False, "error": f"登录处理失败: {str(e)}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    def handle_logout(self, request_handler: 'BaseHTTPRequestHandler') -> Response:
        """处理登出 GET /api/logout"""
        self.auth_manager.logout(request_handler)
        # 重定向到登录页面
        return RedirectResponse('/login')
    
    def handle_user_manage(self, request_handler: 'BaseHTTPRequestHandler') -> Response:
        """显示用户管理页面 GET /admin/users"""
        user_info = self._require_admin(request_handler)
        if not user_info:
            return JsonResponse(
                {"success": False, "error": "需要管理员权限"},
                status=HTTPStatus.FORBIDDEN
            )
        
        users = self.user_service.list_users(include_disabled=True)
        body = render_user_manage_page([u.to_dict() for u in users])
        return HtmlResponse(body)
    
    def handle_create_user(self, form_data: Dict[str, list], request_handler: 'BaseHTTPRequestHandler') -> Response:
        """创建用户 POST /api/admin/users"""
        user_info = self._require_admin(request_handler)
        if not user_info:
            return JsonResponse(
                {"success": False, "error": "需要管理员权限"},
                status=HTTPStatus.FORBIDDEN
            )
        
        username = form_data.get("username", [""])[0].strip()
        password = form_data.get("password", [""])[0].strip()
        is_admin = form_data.get("is_admin", ["false"])[0].lower() == "true"
        
        if not username or not password:
            return JsonResponse(
                {"success": False, "error": "用户名和密码不能为空"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        user = self.user_service.create_user(username, password, is_admin=is_admin)
        if user:
            return JsonResponse({
                "success": True,
                "message": "用户创建成功",
                "user": user.to_dict()
            })
        else:
            return JsonResponse(
                {"success": False, "error": "用户名已存在"},
                status=HTTPStatus.BAD_REQUEST
            )
    
    def handle_delete_user(self, query: Dict[str, list], request_handler: 'BaseHTTPRequestHandler') -> Response:
        """删除用户 DELETE /api/admin/users?id=xxx"""
        user_info = self._require_admin(request_handler)
        if not user_info:
            return JsonResponse(
                {"success": False, "error": "需要管理员权限"},
                status=HTTPStatus.FORBIDDEN
            )
        
        user_id, error_response = self._parse_user_id(query)
        if error_response:
            return error_response
        
        if self.user_service.delete_user(user_id):
            return JsonResponse({"success": True, "message": "用户删除成功"})
        else:
            return JsonResponse(
                {"success": False, "error": "用户不存在"},
                status=HTTPStatus.NOT_FOUND
            )
    
    def handle_get_user_detail(self, query: Dict[str, list], request_handler: 'BaseHTTPRequestHandler') -> Response:
        """获取用户详情 GET /api/admin/users?id=xxx"""
        user_info = self._require_admin(request_handler)
        if not user_info:
            return JsonResponse(
                {"success": False, "error": "需要管理员权限"},
                status=HTTPStatus.FORBIDDEN
            )
        
        user_id, error_response = self._parse_user_id(query)
        if error_response:
            return error_response
        
        user = self.user_service.get_user(user_id=user_id)
        if not user:
            return JsonResponse(
                {"success": False, "error": "用户不存在"},
                status=HTTPStatus.NOT_FOUND
            )
        
        # 获取用户的股票列表
        stock_list = self.user_service.get_user_stock_list(user_id)
        
        user_dict = user.to_dict()
        user_dict['stock_list'] = stock_list
        
        return JsonResponse({
            "success": True,
            "user": user_dict
        })
    
    def handle_update_user_password(self, form_data: Dict[str, list], request_handler: 'BaseHTTPRequestHandler') -> Response:
        """修改用户密码 PUT /api/admin/users/password 或 PUT /api/users/password"""
        user_info = self.auth_manager.check_auth(request_handler)
        if not user_info:
            return JsonResponse(
                {"success": False, "error": "需要登录"},
                status=HTTPStatus.UNAUTHORIZED
            )
        
        # 获取目标用户ID（管理员可以修改任何用户，普通用户只能修改自己）
        target_user_id_list = form_data.get("user_id", [])
        if target_user_id_list:
            # 管理员修改其他用户密码
            if not user_info.get('is_admin'):
                return JsonResponse(
                    {"success": False, "error": "需要管理员权限"},
                    status=HTTPStatus.FORBIDDEN
                )
            try:
                target_user_id = int(target_user_id_list[0])
            except ValueError:
                return JsonResponse(
                    {"success": False, "error": "无效的用户ID"},
                    status=HTTPStatus.BAD_REQUEST
                )
        else:
            # 普通用户修改自己的密码
            target_user_id = user_info['user_id']
        
        password = form_data.get("password", [""])[0].strip()
        if not password:
            return JsonResponse(
                {"success": False, "error": "密码不能为空"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        if self.user_service.update_user(target_user_id, password=password):
            return JsonResponse({"success": True, "message": "密码修改成功"})
        else:
            return JsonResponse(
                {"success": False, "error": "用户不存在"},
                status=HTTPStatus.NOT_FOUND
            )
    
    def handle_update_user_role(self, form_data: Dict[str, list], request_handler: 'BaseHTTPRequestHandler') -> Response:
        """修改用户角色 PUT /api/admin/users/role"""
        user_info = self._require_admin(request_handler)
        if not user_info:
            return JsonResponse(
                {"success": False, "error": "需要管理员权限"},
                status=HTTPStatus.FORBIDDEN
            )
        
        user_id, error_response = self._parse_user_id(form_data, "user_id")
        if error_response:
            return error_response
        
        is_admin_str = form_data.get("is_admin", ["false"])[0].lower()
        is_admin = is_admin_str == "true"
        
        if self.user_service.update_user(user_id, is_admin=is_admin):
            return JsonResponse({"success": True, "message": "角色修改成功"})
        else:
            return JsonResponse(
                {"success": False, "error": "用户不存在"},
                status=HTTPStatus.NOT_FOUND
            )
    
    def handle_update_user_status(self, form_data: Dict[str, list], request_handler: 'BaseHTTPRequestHandler') -> Response:
        """启用/禁用用户 PUT /api/admin/users/status"""
        user_info = self._require_admin(request_handler)
        if not user_info:
            return JsonResponse(
                {"success": False, "error": "需要管理员权限"},
                status=HTTPStatus.FORBIDDEN
            )
        
        user_id, error_response = self._parse_user_id(form_data, "user_id")
        if error_response:
            return error_response
        
        enabled_str = form_data.get("enabled", ["true"])[0].lower()
        enabled = enabled_str == "true"
        
        if self.user_service.update_user(user_id, enabled=enabled):
            return JsonResponse({"success": True, "message": "状态修改成功"})
        else:
            return JsonResponse(
                {"success": False, "error": "用户不存在"},
                status=HTTPStatus.NOT_FOUND
            )


# ============================================================
# Bot Webhook 处理器
# ============================================================

class BotHandler:
    """
    机器人 Webhook 处理器
    
    处理各平台的机器人回调请求。
    """
    
    def handle_webhook(self, platform: str, form_data: Dict[str, list], headers: Dict[str, str], body: bytes) -> Response:
        """
        处理 Webhook 请求
        
        Args:
            platform: 平台名称 (feishu, dingtalk, wecom, telegram)
            form_data: POST 数据（已解析）
            headers: HTTP 请求头
            body: 原始请求体
            
        Returns:
            Response 对象
        """
        try:
            from bot.handler import handle_webhook
            from bot.models import WebhookResponse
            
            # 调用 bot 模块处理
            webhook_response = handle_webhook(platform, headers, body)
            
            # 转换为 web 响应
            return JsonResponse(
                webhook_response.body,
                status=HTTPStatus(webhook_response.status_code)
            )
            
        except ImportError as e:
            logger.error(f"[BotHandler] Bot 模块未正确安装: {e}")
            return JsonResponse(
                {"error": "Bot module not available"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"[BotHandler] 处理 {platform} Webhook 失败: {e}")
            return JsonResponse(
                {"error": str(e)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )


# ============================================================
# 处理器工厂
# ============================================================

_page_handler: PageHandler | None = None
_api_handler: ApiHandler | None = None
_bot_handler: BotHandler | None = None
_user_handler: UserHandler | None = None


def get_page_handler() -> PageHandler:
    """获取页面处理器实例"""
    global _page_handler
    if _page_handler is None:
        _page_handler = PageHandler()
    return _page_handler


def get_api_handler() -> ApiHandler:
    """获取 API 处理器实例"""
    global _api_handler
    if _api_handler is None:
        _api_handler = ApiHandler()
    return _api_handler


def get_bot_handler() -> BotHandler:
    """获取 Bot 处理器实例"""
    global _bot_handler
    if _bot_handler is None:
        _bot_handler = BotHandler()
    return _bot_handler


def get_user_handler() -> UserHandler:
    """获取用户管理处理器实例"""
    global _user_handler
    if _user_handler is None:
        _user_handler = UserHandler()
    return _user_handler
