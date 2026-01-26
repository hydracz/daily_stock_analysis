# -*- coding: utf-8 -*-
"""
===================================
Web 服务器核心
===================================

职责：
1. 启动 HTTP 服务器
2. 处理请求分发
3. 提供后台运行接口
"""

from __future__ import annotations

import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Type

from web.router import Router, get_router

logger = logging.getLogger(__name__)


# ============================================================
# HTTP 请求处理器
# ============================================================

class WebRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP 请求处理器
    
    将请求分发到路由器处理
    """
    
    # 类级别的路由器引用
    router: Router = None  # type: ignore
    
    # 使用 HTTP/1.1 协议版本
    protocol_version = "HTTP/1.1"
    
    def parse_request(self):
        """解析请求，确保 request_version 正确设置"""
        result = super().parse_request()
        # 如果解析成功，确保 request_version 不是 HTTP/0.9
        if result and hasattr(self, 'request_version'):
            if self.request_version == 'HTTP/0.9':
                logger.warning(f"[WebRequestHandler] 检测到 HTTP/0.9 请求，强制升级为 HTTP/1.1")
                self.request_version = 'HTTP/1.1'
            # 确保 protocol_version 与 request_version 一致
            if self.protocol_version != "HTTP/1.1":
                self.protocol_version = "HTTP/1.1"
        return result
    
    def do_GET(self) -> None:
        """处理 GET 请求"""
        # 确保使用 HTTP/1.1（必须在处理请求前设置）
        self.protocol_version = "HTTP/1.1"
        try:
            self.router.dispatch(self, "GET")
        except Exception as e:
            logger.error(f"[WebRequestHandler] GET 请求处理异常: {e}", exc_info=True)
            try:
                self.send_error(500, "Internal Server Error")
            except Exception:
                pass
    
    def do_POST(self) -> None:
        """处理 POST 请求"""
        # 确保使用 HTTP/1.1（必须在处理请求前设置）
        self.protocol_version = "HTTP/1.1"
        try:
            self.router.dispatch_post(self)
        except Exception as e:
            logger.error(f"[WebRequestHandler] POST 请求处理异常: {e}", exc_info=True)
            try:
                self.send_error(500, "Internal Server Error")
            except Exception:
                pass
    
    def do_OPTIONS(self) -> None:
        """处理 OPTIONS 请求（CORS 预检）"""
        # 确保使用 HTTP/1.1
        self.protocol_version = "HTTP/1.1"
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.end_headers()
    
    def log_message(self, fmt: str, *args) -> None:
        """自定义日志格式（使用 logging 而非 stderr）"""
        # 可以取消注释以启用请求日志
        # logger.debug(f"[WebServer] {self.address_string()} - {fmt % args}")
        pass


# ============================================================
# Web 服务器
# ============================================================

class WebServer:
    """
    Web 服务器
    
    封装 ThreadingHTTPServer，提供便捷的启动和管理接口
    
    使用方式：
        # 前台运行
        server = WebServer(host="127.0.0.1", port=8000)
        server.run()
        
        # 后台运行
        server = WebServer(host="127.0.0.1", port=8000)
        server.start_background()
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        router: Optional[Router] = None
    ):
        """
        初始化 Web 服务器
        
        Args:
            host: 监听地址
            port: 监听端口
            router: 路由器实例（可选，默认使用全局路由）
        """
        self.host = host
        self.port = port
        self.router = router or get_router()
        
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
    
    @property
    def address(self) -> str:
        """服务器地址"""
        return f"http://{self.host}:{self.port}"
    
    def _create_handler_class(self) -> Type[WebRequestHandler]:
        """创建带路由器引用的处理器类"""
        router = self.router
        
        class Handler(WebRequestHandler):
            # 确保使用 HTTP/1.1 协议版本
            protocol_version = "HTTP/1.1"
            pass
        
        Handler.router = router
        return Handler
    
    def _create_server(self) -> ThreadingHTTPServer:
        """创建 HTTP 服务器实例"""
        handler_class = self._create_handler_class()
        return ThreadingHTTPServer((self.host, self.port), handler_class)
    
    def run(self) -> None:
        """
        前台运行服务器（阻塞）
        
        按 Ctrl+C 退出
        """
        self._server = self._create_server()
        
        logger.info(f"WebUI 服务启动: {self.address}")
        print(f"WebUI 服务启动: {self.address}")
        
        # 打印路由列表
        routes = self.router.list_routes()
        if routes:
            logger.info("已注册路由:")
            for method, path, desc in routes:
                logger.info(f"  {method:6} {path:20} - {desc}")
        
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            logger.info("收到退出信号，服务器关闭")
        finally:
            self._server.server_close()
            self._server = None
    
    def start_background(self) -> threading.Thread:
        """
        后台运行服务器（非阻塞）
        
        Returns:
            服务器线程
        """
        self._server = self._create_server()
        
        def serve():
            logger.info(f"WebUI 已启动: {self.address}")
            print(f"WebUI 已启动: {self.address}")
            try:
                self._server.serve_forever()
            except Exception as e:
                logger.error(f"WebUI 发生错误: {e}")
            finally:
                if self._server:
                    self._server.server_close()
        
        self._thread = threading.Thread(target=serve, daemon=True)
        self._thread.start()
        return self._thread
    
    def stop(self) -> None:
        """停止服务器"""
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
            logger.info("WebUI 服务已停止")
    
    def is_running(self) -> bool:
        """检查服务器是否运行中"""
        return self._server is not None


# ============================================================
# 便捷函数
# ============================================================

def run_server_in_thread(
    host: str = "127.0.0.1",
    port: int = 8000,
    router: Optional[Router] = None
) -> threading.Thread:
    """
    在后台线程启动 WebUI 服务器
    
    Args:
        host: 监听地址
        port: 监听端口
        router: 路由器实例（可选）
        
    Returns:
        服务器线程
    """
    server = WebServer(host=host, port=port, router=router)
    return server.start_background()


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    router: Optional[Router] = None
) -> None:
    """
    前台运行 WebUI 服务器（阻塞）
    
    Args:
        host: 监听地址
        port: 监听端口
        router: 路由器实例（可选）
    """
    server = WebServer(host=host, port=port, router=router)
    server.run()
