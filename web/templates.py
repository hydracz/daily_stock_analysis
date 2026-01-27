# -*- coding: utf-8 -*-
"""
===================================
Web 模板层 - HTML 页面生成
===================================

职责：
1. 生成 HTML 页面
2. 管理 CSS 样式
3. 提供可复用的页面组件
"""

from __future__ import annotations

import html
from typing import Optional


# ============================================================
# CSS 样式定义
# ============================================================

BASE_CSS = """
:root {
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #1e293b;
    --text-light: #64748b;
    --border: #e2e8f0;
    --success: #10b981;
    --error: #ef4444;
    --warning: #f59e0b;
}

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg);
    color: var(--text);
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    margin: 0;
    padding: 20px;
}

.container {
    background: var(--card);
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    width: 100%;
    max-width: 500px;
}

h2 {
    margin-top: 0;
    color: var(--text);
    font-size: 1.5rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.subtitle {
    color: var(--text-light);
    font-size: 0.875rem;
    margin-bottom: 2rem;
    line-height: 1.5;
}

.code-badge {
    background: #f1f5f9;
    padding: 0.2rem 0.4rem;
    border-radius: 0.25rem;
    font-family: monospace;
    color: var(--primary);
}

.form-group {
    margin-bottom: 1.5rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text);
}

textarea, input[type="text"] {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    font-family: monospace;
    font-size: 0.875rem;
    line-height: 1.5;
    resize: vertical;
    transition: border-color 0.2s, box-shadow 0.2s;
}

textarea:focus, input[type="text"]:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

button {
    background-color: var(--primary);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    width: 100%;
    font-size: 1rem;
}

button:hover {
    background-color: var(--primary-hover);
    transform: translateY(-1px);
}

button:active {
    transform: translateY(0);
}

.btn-secondary {
    background-color: var(--text-light);
}

.btn-secondary:hover {
    background-color: var(--text);
}

.footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    color: var(--text-light);
    font-size: 0.75rem;
    text-align: center;
}

/* Toast Notification */
.toast {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: white;
    border-left: 4px solid var(--success);
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    opacity: 0;
    z-index: 1000;
}

.toast.show {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
}

.toast.error {
    border-left-color: var(--error);
}

.toast.warning {
    border-left-color: var(--warning);
}

/* Helper classes */
.text-muted {
    font-size: 0.75rem;
    color: var(--text-light);
    margin-top: 0.5rem;
}

.mt-2 { margin-top: 0.5rem; }
.mt-4 { margin-top: 1rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }

/* Section divider */
.section-divider {
    margin: 2rem 0;
    border: none;
    border-top: 1px solid var(--border);
}

/* Analysis section */
.analysis-section {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
}

.analysis-section h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text);
}

.input-group {
    display: flex;
    gap: 0.5rem;
}

.input-group input {
    flex: 1;
    resize: none;
}

.input-group button {
    width: auto;
    padding: 0.75rem 1.25rem;
    white-space: nowrap;
}

.report-select {
    padding: 0.75rem 0.5rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    font-size: 0.8rem;
    background: white;
    color: var(--text);
    cursor: pointer;
    min-width: 110px;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.report-select:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.btn-analysis {
    background-color: var(--success);
}

.btn-analysis:hover {
    background-color: #059669;
}

.btn-analysis:disabled {
    background-color: var(--text-light);
    cursor: not-allowed;
    transform: none;
}

/* Result box */
.result-box {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    display: none;
}

.result-box.show {
    display: block;
}

.result-box.success {
    background-color: #ecfdf5;
    border: 1px solid #a7f3d0;
    color: #065f46;
}

.result-box.error {
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    color: #991b1b;
}

.result-box.loading {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1e40af;
}

.spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
    margin-right: 0.5rem;
    vertical-align: middle;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Task List Container */
.task-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-height: 400px;
    overflow-y: auto;
}

.task-list:empty::after {
    content: '暂无任务';
    display: block;
    text-align: center;
    color: var(--text-light);
    font-size: 0.8rem;
    padding: 1rem;
}

/* Task Card - Compact */
.task-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.75rem;
    background: var(--bg);
    border-radius: 0.5rem;
    border: 1px solid var(--border);
    font-size: 0.8rem;
    transition: all 0.2s;
}

.task-card:hover {
    border-color: var(--primary);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.task-card.running {
    border-color: var(--primary);
    background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
}

.task-card.completed {
    border-color: var(--success);
    background: linear-gradient(135deg, #ecfdf5 0%, #f8fafc 100%);
}

.task-card.failed {
    border-color: var(--error);
    background: linear-gradient(135deg, #fef2f2 0%, #f8fafc 100%);
}

/* Task Status Icon */
.task-status {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    flex-shrink: 0;
    font-size: 0.9rem;
}

.task-card.running .task-status {
    background: var(--primary);
    color: white;
}

.task-card.completed .task-status {
    background: var(--success);
    color: white;
}

.task-card.failed .task-status {
    background: var(--error);
    color: white;
}

.task-card.pending .task-status {
    background: var(--border);
    color: var(--text-light);
}

/* Task Main Info */
.task-main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.task-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--text);
}

.task-title .code {
    font-family: monospace;
    background: rgba(0,0,0,0.05);
    padding: 0.1rem 0.3rem;
    border-radius: 0.25rem;
}

.task-title .name {
    color: var(--text-light);
    font-weight: 400;
    font-size: 0.75rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.task-meta {
    display: flex;
    gap: 0.75rem;
    font-size: 0.7rem;
    color: var(--text-light);
}

.task-meta span {
    display: flex;
    align-items: center;
    gap: 0.2rem;
}

.task-progress {
    color: var(--primary);
    font-weight: 500;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* Task Result Badge */
.task-result {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.15rem;
    flex-shrink: 0;
}

.task-advice {
    font-weight: 600;
    font-size: 0.75rem;
    padding: 0.15rem 0.4rem;
    border-radius: 0.25rem;
    background: var(--primary);
    color: white;
}

.task-advice.buy { background: #059669; }
.task-advice.sell { background: #dc2626; }
.task-advice.hold { background: #d97706; }
.task-advice.wait { background: #6b7280; }

.task-score {
    font-size: 0.7rem;
    color: var(--text-light);
}

/* Task Actions */
.task-actions {
    display: flex;
    gap: 0.25rem;
    flex-shrink: 0;
}

.task-btn {
    width: 24px;
    height: 24px;
    padding: 0;
    border-radius: 0.25rem;
    background: transparent;
    color: var(--text-light);
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.task-btn:hover {
    background: rgba(0,0,0,0.05);
    color: var(--text);
    transform: none;
}

/* Spinner in task */
.task-card .spinner {
    width: 12px;
    height: 12px;
    border-width: 1.5px;
    margin: 0;
}

/* Empty state hint */
.task-hint {
    text-align: center;
    padding: 0.75rem;
    color: var(--text-light);
    font-size: 0.75rem;
    background: var(--bg);
    border-radius: 0.375rem;
}

/* Task detail expand */
.task-detail {
    display: none;
    padding: 0.5rem 0.75rem;
    padding-left: 3rem;
    background: rgba(0,0,0,0.02);
    border-radius: 0 0 0.5rem 0.5rem;
    margin-top: -0.5rem;
    font-size: 0.75rem;
    border: 1px solid var(--border);
    border-top: none;
}

.task-detail.show {
    display: block;
}

.task-detail-row {
    display: flex;
    justify-content: space-between;
    padding: 0.25rem 0;
}

.task-detail-row .label {
    color: var(--text-light);
}

.task-detail-summary {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: white;
    border-radius: 0.25rem;
    line-height: 1.4;
}

.task-detail-section {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border);
}

.task-detail-section:first-child {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
}

.task-detail-section h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text);
}

.task-detail-text {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: white;
    border-radius: 0.25rem;
    line-height: 1.5;
    font-size: 0.75rem;
    color: var(--text);
    white-space: pre-wrap;
    word-wrap: break-word;
}
"""


# ============================================================
# 页面模板
# ============================================================

def render_base(
    title: str,
    content: str,
    extra_css: str = "",
    extra_js: str = ""
) -> str:
    """
    渲染基础 HTML 模板
    
    Args:
        title: 页面标题
        content: 页面内容 HTML
        extra_css: 额外的 CSS 样式
        extra_js: 额外的 JavaScript
    """
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>{BASE_CSS}{extra_css}</style>
</head>
<body>
  {content}
  {extra_js}
</body>
</html>"""


def render_toast(message: str, toast_type: str = "success") -> str:
    """
    渲染 Toast 通知
    
    Args:
        message: 通知消息
        toast_type: 类型 (success, error, warning)
    """
    icon_map = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️"
    }
    icon = icon_map.get(toast_type, "ℹ️")
    type_class = f" {toast_type}" if toast_type != "success" else ""
    
    return f"""
    <div id="toast" class="toast show{type_class}">
        <span class="icon">{icon}</span> {html.escape(message)}
    </div>
    <script>
        setTimeout(() => {{
            document.getElementById('toast').classList.remove('show');
        }}, 3000);
    </script>
    """


def render_config_page(
    stock_list: str,
    env_filename: str,
    message: Optional[str] = None,
    current_user: str = "guest",
    is_admin: bool = False
) -> bytes:
    """
    渲染配置页面
    
    Args:
        stock_list: 当前自选股列表
        env_filename: 环境文件名
        message: 可选的提示消息
    """
    safe_value = html.escape(stock_list)
    toast_html = render_toast(message) if message else ""
    
    # 用户信息区域（如果已登录）
    user_info_html = ""
    password_modal_html = ""
    if current_user != "guest":
        admin_link = f'<a href="/admin/users" style="color: var(--primary); text-decoration: none; margin-left: 10px;">👥 用户管理</a>' if is_admin else ""
        user_info_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid var(--border);">
        <div>
            <span style="color: var(--text-light);">当前用户: <strong>{html.escape(current_user)}</strong></span>
            {admin_link}
        </div>
        <div>
            <button onclick="showChangePasswordModal()" 
                    style="padding: 6px 12px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                🔑 修改密码
            </button>
            <a href="/api/logout" 
               style="padding: 6px 12px; margin-left: 8px; background: var(--text-light); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; text-decoration: none; display: inline-block;">
                🚪 退出
            </a>
        </div>
    </div>
        """
        
        # 修改密码模态框
        password_modal_html = """
    <!-- 修改密码模态框 -->
    <div id="changePasswordModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
        <div style="background: white; padding: 30px; border-radius: 8px; max-width: 400px; margin: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="margin-top: 0;">修改密码</h3>
            <form id="changePasswordForm" onsubmit="changePassword(event)">
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 500;">新密码</label>
                    <input type="password" id="changePasswordInput" name="password" required 
                           style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box;">
                </div>
                <div id="changePasswordMsg" style="display: none; margin-bottom: 15px; padding: 10px; border-radius: 4px;"></div>
                <div style="display: flex; gap: 10px;">
                    <button type="submit" 
                            style="flex: 1; padding: 10px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                        确定
                    </button>
                    <button type="button" onclick="closeChangePasswordModal()" 
                            style="flex: 1; padding: 10px; background: var(--text-light); color: white; border: none; border-radius: 4px; cursor: pointer;">
                        取消
                    </button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function showChangePasswordModal() {
            document.getElementById('changePasswordModal').style.display = 'flex';
            document.getElementById('changePasswordInput').value = '';
            document.getElementById('changePasswordMsg').style.display = 'none';
        }
        
        function closeChangePasswordModal() {
            document.getElementById('changePasswordModal').style.display = 'none';
            document.getElementById('changePasswordForm').reset();
        }
        
        async function changePassword(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            const msgDiv = document.getElementById('changePasswordMsg');
            
            try {
                const response = await fetch('/api/users/password', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                msgDiv.style.display = 'block';
                if (result.success) {
                    msgDiv.textContent = '密码修改成功';
                    msgDiv.style.background = '#059669';
                    msgDiv.style.color = 'white';
                    setTimeout(() => {
                        closeChangePasswordModal();
                        alert('密码修改成功，请重新登录');
                        window.location.href = '/api/logout';
                    }, 1500);
                } else {
                    msgDiv.textContent = result.error || '密码修改失败';
                    msgDiv.style.background = '#dc2626';
                    msgDiv.style.color = 'white';
                }
            } catch (error) {
                msgDiv.style.display = 'block';
                msgDiv.textContent = '网络错误: ' + error.message;
                msgDiv.style.background = '#dc2626';
                msgDiv.style.color = 'white';
            }
        }
        
        // 点击模态框外部关闭
        document.addEventListener('click', function(e) {
            if (e.target.id === 'changePasswordModal') {
                closeChangePasswordModal();
            }
        });
    </script>
        """
    
    # 分析组件的 JavaScript - 支持多任务
    analysis_js = """
<script>
(function() {
    const codeInput = document.getElementById('analysis_code');
    const submitBtn = document.getElementById('analysis_btn');
    const taskList = document.getElementById('task_list');
    const reportTypeSelect = document.getElementById('report_type');
    
    // 任务管理
    const tasks = new Map(); // taskId -> {task, pollCount}
    let pollInterval = null;
    const MAX_POLL_COUNT = 120; // 6 分钟超时：120 * 3000ms = 360000ms
    const POLL_INTERVAL_MS = 3000;
    const MAX_TASKS_DISPLAY = 10;
    
    // 允许输入数字和字母（支持港股 hkxxxxx 格式）
    codeInput.addEventListener('input', function(e) {
        // 转小写，只保留字母和数字
        this.value = this.value.toLowerCase().replace(/[^a-z0-9]/g, '');
        if (this.value.length > 8) {
            this.value = this.value.slice(0, 8);
        }
        updateButtonState();
    });
    
    // 回车提交
    codeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (!submitBtn.disabled) {
                submitAnalysis();
            }
        }
    });
    
    // 更新按钮状态 - 支持 A股(6位数字) 或 港股(hk+5位数字)
    function updateButtonState() {
        const code = codeInput.value.trim().toLowerCase();
        const isAStock = /^\\d{6}$/.test(code);           // A股: 600519
        const isHKStock = /^hk\\d{5}$/.test(code);        // 港股: hk00700
        submitBtn.disabled = !(isAStock || isHKStock);
    }
    
    // 格式化时间
    function formatTime(isoString) {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit', second: '2-digit'});
    }
    
    // 计算耗时
    function calcDuration(start, end) {
        if (!start) return '-';
        const startTime = new Date(start).getTime();
        const endTime = end ? new Date(end).getTime() : Date.now();
        const seconds = Math.floor((endTime - startTime) / 1000);
        if (seconds < 60) return seconds + 's';
        const minutes = Math.floor(seconds / 60);
        const remainSec = seconds % 60;
        return minutes + 'm' + remainSec + 's';
    }
    
    // 获取建议样式类
    function getAdviceClass(advice) {
        if (!advice) return '';
        if (advice.includes('买') || advice.includes('加仓')) return 'buy';
        if (advice.includes('卖') || advice.includes('减仓')) return 'sell';
        if (advice.includes('持有')) return 'hold';
        return 'wait';
    }
    
    // 渲染单个任务卡片
    function renderTaskCard(taskId, taskData) {
        const task = taskData.task || {};
        const status = task.status || 'pending';
        const code = task.code || taskId.split('_')[0];
        const result = task.result || {};
        
        let statusIcon = '⏳';
        let statusText = '等待中';
        if (status === 'running') { 
            statusIcon = '<span class="spinner"></span>'; 
            statusText = '分析中';
            // 显示进度信息
            if (task.progress) {
                statusText = task.progress;
            }
        }
        else if (status === 'completed') { statusIcon = '✓'; statusText = '完成'; }
        else if (status === 'failed') { statusIcon = '✗'; statusText = '失败'; }
        
        let resultHtml = '';
        if (status === 'completed' && result.operation_advice) {
            const adviceClass = getAdviceClass(result.operation_advice);
            resultHtml = '<div class="task-result">' +
                '<span class="task-advice ' + adviceClass + '">' + result.operation_advice + '</span>' +
                '<span class="task-score">' + (result.sentiment_score || '-') + '分</span>' +
                '</div>';
        } else if (status === 'failed') {
            resultHtml = '<div class="task-result"><span class="task-advice sell">失败</span></div>';
        }
        
        let detailHtml = '';
        if (status === 'completed') {
            const isFullReport = task.report_type === 'full';
            let detailContent = '';
            
            if (isFullReport) {
                // 完整报告：显示所有详细分析内容
                detailContent = '<div class="task-detail-row"><span class="label">趋势</span><span>' + (result.trend_prediction || '-') + '</span></div>' +
                    '<div class="task-detail-row"><span class="label">置信度</span><span>' + (result.confidence_level || '-') + '</span></div>';
                
                // 决策仪表盘
                if (result.dashboard) {
                    const dashboard = result.dashboard;
                    if (dashboard.core_conclusion) {
                        const core = dashboard.core_conclusion;
                        detailContent += '<div class="task-detail-section"><h4>📊 核心结论</h4>' +
                            '<div class="task-detail-row"><span class="label">一句话结论</span><span>' + (core.one_sentence || '-') + '</span></div>' +
                            '<div class="task-detail-row"><span class="label">信号类型</span><span>' + (core.signal_type || '-') + '</span></div>' +
                            '<div class="task-detail-row"><span class="label">时间敏感度</span><span>' + (core.time_sensitivity || '-') + '</span></div>';
                        if (core.position_advice) {
                            detailContent += '<div class="task-detail-row"><span class="label">空仓建议</span><span>' + (core.position_advice.no_position || '-') + '</span></div>' +
                                '<div class="task-detail-row"><span class="label">持仓建议</span><span>' + (core.position_advice.has_position || '-') + '</span></div>';
                        }
                        detailContent += '</div>';
                    }
                    
                    if (dashboard.data_perspective) {
                        const data = dashboard.data_perspective;
                        detailContent += '<div class="task-detail-section"><h4>📈 数据视角</h4>';
                        if (data.trend_status) {
                            detailContent += '<div class="task-detail-row"><span class="label">均线排列</span><span>' + (data.trend_status.ma_alignment || '-') + '</span></div>' +
                                '<div class="task-detail-row"><span class="label">趋势评分</span><span>' + (data.trend_status.trend_score || '-') + '</span></div>';
                        }
                        if (data.price_position) {
                            detailContent += '<div class="task-detail-row"><span class="label">当前价格</span><span>' + (data.price_position.current_price || '-') + '</span></div>' +
                                '<div class="task-detail-row"><span class="label">MA5</span><span>' + (data.price_position.ma5 || '-') + '</span></div>' +
                                '<div class="task-detail-row"><span class="label">乖离率</span><span>' + (data.price_position.bias_ma5 || '-') + '%</span></div>' +
                                '<div class="task-detail-row"><span class="label">乖离状态</span><span>' + (data.price_position.bias_status || '-') + '</span></div>';
                        }
                        if (data.chip_structure) {
                            detailContent += '<div class="task-detail-row"><span class="label">获利比例</span><span>' + (data.chip_structure.profit_ratio || '-') + '%</span></div>' +
                                '<div class="task-detail-row"><span class="label">筹码健康度</span><span>' + (data.chip_structure.chip_health || '-') + '</span></div>';
                        }
                        detailContent += '</div>';
                    }
                    
                    if (dashboard.intelligence) {
                        const intel = dashboard.intelligence;
                        detailContent += '<div class="task-detail-section"><h4>🔍 情报分析</h4>';
                        if (intel.latest_news) {
                            detailContent += '<div class="task-detail-row"><span class="label">最新消息</span><span>' + intel.latest_news + '</span></div>';
                        }
                        if (intel.risk_alerts && intel.risk_alerts.length > 0) {
                            detailContent += '<div class="task-detail-row"><span class="label">风险警报</span><span>' + intel.risk_alerts.join('; ') + '</span></div>';
                        }
                        if (intel.positive_catalysts && intel.positive_catalysts.length > 0) {
                            detailContent += '<div class="task-detail-row"><span class="label">利好因素</span><span>' + intel.positive_catalysts.join('; ') + '</span></div>';
                        }
                        if (intel.earnings_outlook) {
                            detailContent += '<div class="task-detail-row"><span class="label">业绩预期</span><span>' + intel.earnings_outlook + '</span></div>';
                        }
                        detailContent += '</div>';
                    }
                    
                    if (dashboard.battle_plan) {
                        const plan = dashboard.battle_plan;
                        detailContent += '<div class="task-detail-section"><h4>🎯 作战计划</h4>';
                        if (plan.sniper_points) {
                            detailContent += '<div class="task-detail-row"><span class="label">理想买入点</span><span>' + (plan.sniper_points.ideal_buy || '-') + '</span></div>' +
                                '<div class="task-detail-row"><span class="label">次优买入点</span><span>' + (plan.sniper_points.secondary_buy || '-') + '</span></div>' +
                                '<div class="task-detail-row"><span class="label">止损位</span><span>' + (plan.sniper_points.stop_loss || '-') + '</span></div>' +
                                '<div class="task-detail-row"><span class="label">目标位</span><span>' + (plan.sniper_points.take_profit || '-') + '</span></div>';
                        }
                        if (plan.action_checklist && plan.action_checklist.length > 0) {
                            detailContent += '<div class="task-detail-row"><span class="label">检查清单</span><span>' + plan.action_checklist.join(' | ') + '</span></div>';
                        }
                        detailContent += '</div>';
                    }
                }
                
                // 详细分析内容
                if (result.technical_analysis) {
                    detailContent += '<div class="task-detail-section"><h4>📊 技术面分析</h4>' +
                        '<div class="task-detail-text">' + result.technical_analysis + '</div></div>';
                }
                if (result.ma_analysis) {
                    detailContent += '<div class="task-detail-section"><h4>📈 均线分析</h4>' +
                        '<div class="task-detail-text">' + result.ma_analysis + '</div></div>';
                }
                if (result.volume_analysis) {
                    detailContent += '<div class="task-detail-section"><h4>📊 量能分析</h4>' +
                        '<div class="task-detail-text">' + result.volume_analysis + '</div></div>';
                }
                if (result.trend_analysis) {
                    detailContent += '<div class="task-detail-section"><h4>📉 走势分析</h4>' +
                        '<div class="task-detail-text">' + result.trend_analysis + '</div></div>';
                }
                if (result.short_term_outlook) {
                    detailContent += '<div class="task-detail-section"><h4>⏰ 短期展望</h4>' +
                        '<div class="task-detail-text">' + result.short_term_outlook + '</div></div>';
                }
                if (result.medium_term_outlook) {
                    detailContent += '<div class="task-detail-section"><h4>📅 中期展望</h4>' +
                        '<div class="task-detail-text">' + result.medium_term_outlook + '</div></div>';
                }
                if (result.fundamental_analysis) {
                    detailContent += '<div class="task-detail-section"><h4>🏢 基本面分析</h4>' +
                        '<div class="task-detail-text">' + result.fundamental_analysis + '</div></div>';
                }
                if (result.news_summary) {
                    detailContent += '<div class="task-detail-section"><h4>📰 新闻摘要</h4>' +
                        '<div class="task-detail-text">' + result.news_summary + '</div></div>';
                }
                if (result.key_points) {
                    detailContent += '<div class="task-detail-section"><h4>💡 核心看点</h4>' +
                        '<div class="task-detail-text">' + result.key_points + '</div></div>';
                }
                if (result.risk_warning) {
                    detailContent += '<div class="task-detail-section"><h4>⚠️ 风险提示</h4>' +
                        '<div class="task-detail-text">' + result.risk_warning + '</div></div>';
                }
                if (result.buy_reason) {
                    detailContent += '<div class="task-detail-section"><h4>💭 操作理由</h4>' +
                        '<div class="task-detail-text">' + result.buy_reason + '</div></div>';
                }
                if (result.analysis_summary) {
                    detailContent += '<div class="task-detail-section"><h4>📝 综合分析</h4>' +
                        '<div class="task-detail-text">' + result.analysis_summary + '</div></div>';
                }
            } else {
                // 精简报告：只显示核心信息
                detailContent = '<div class="task-detail-row"><span class="label">趋势</span><span>' + (result.trend_prediction || '-') + '</span></div>' +
                    (result.analysis_summary ? '<div class="task-detail-summary">' + result.analysis_summary.substring(0, 200) + (result.analysis_summary.length > 200 ? '...' : '') + '</div>' : '');
            }
            
            detailHtml = '<div class="task-detail" id="detail_' + taskId + '">' + detailContent + '</div>';
        }
        
        return '<div class="task-card ' + status + '" id="task_' + taskId + '" onclick="toggleDetail(\\''+taskId+'\\')">' +
            '<div class="task-status">' + statusIcon + '</div>' +
            '<div class="task-main">' +
                '<div class="task-title">' +
                    '<span class="code">' + code + '</span>' +
                    '<span class="name">' + (result.name || code) + '</span>' +
                '</div>' +
                '<div class="task-meta">' +
                    '<span>⏱ ' + formatTime(task.start_time) + '</span>' +
                    '<span>⏳ ' + calcDuration(task.start_time, task.end_time) + '</span>' +
                    '<span>' + (task.report_type === 'full' ? '📊完整' : '📝精简') + '</span>' +
                    (status === 'running' && task.progress ? '<span class="task-progress">' + task.progress + '</span>' : '') +
                '</div>' +
            '</div>' +
            resultHtml +
            '<div class="task-actions">' +
                '<button class="task-btn" onclick="event.stopPropagation();removeTask(\\''+taskId+'\\')">×</button>' +
            '</div>' +
        '</div>' + detailHtml;
    }
    
    // 渲染所有任务
    function renderAllTasks() {
        if (tasks.size === 0) {
            taskList.innerHTML = '<div class="task-hint">💡 输入股票代码开始分析</div>';
            return;
        }
        
        let html = '';
        const sortedTasks = Array.from(tasks.entries())
            .sort((a, b) => (b[1].task?.start_time || '').localeCompare(a[1].task?.start_time || ''));
        
        sortedTasks.slice(0, MAX_TASKS_DISPLAY).forEach(([taskId, taskData]) => {
            html += renderTaskCard(taskId, taskData);
        });
        
        if (sortedTasks.length > MAX_TASKS_DISPLAY) {
            html += '<div class="task-hint">... 还有 ' + (sortedTasks.length - MAX_TASKS_DISPLAY) + ' 个任务</div>';
        }
        
        taskList.innerHTML = html;
    }
    
    // 切换详情显示
    window.toggleDetail = function(taskId) {
        const detail = document.getElementById('detail_' + taskId);
        if (detail) {
            detail.classList.toggle('show');
        }
    };
    
    // 移除任务
    window.removeTask = function(taskId) {
        tasks.delete(taskId);
        renderAllTasks();
        checkStopPolling();
    };
    
    // 轮询所有运行中的任务
    function pollAllTasks() {
        let hasRunning = false;
        
        tasks.forEach((taskData, taskId) => {
            const status = taskData.task?.status;
            if (status === 'running' || status === 'pending' || !status) {
                hasRunning = true;
                taskData.pollCount = (taskData.pollCount || 0) + 1;
                
                if (taskData.pollCount > MAX_POLL_COUNT) {
                    taskData.task = taskData.task || {};
                    taskData.task.status = 'failed';
                    taskData.task.error = '轮询超时';
                    return;
                }
                
                fetch('/task?id=' + encodeURIComponent(taskId))
                    .then(r => r.json())
                    .then(data => {
                        if (data.success && data.task) {
                            taskData.task = data.task;
                            renderAllTasks();
                        }
                    })
                    .catch(() => {});
            }
        });
        
        if (!hasRunning) {
            checkStopPolling();
        }
    }
    
    // 检查是否需要停止轮询
    function checkStopPolling() {
        let hasRunning = false;
        tasks.forEach((taskData) => {
            const status = taskData.task?.status;
            if (status === 'running' || status === 'pending' || !status) {
                hasRunning = true;
            }
        });
        
        if (!hasRunning && pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }
    
    // 开始轮询
    function startPolling() {
        if (!pollInterval) {
            pollInterval = setInterval(pollAllTasks, POLL_INTERVAL_MS);
        }
    }
    
    // 提交分析
    window.submitAnalysis = function() {
        const code = codeInput.value.trim().toLowerCase();
        const isAStock = /^\d{6}$/.test(code);
        const isHKStock = /^hk\d{5}$/.test(code);
        
        if (!(isAStock || isHKStock)) {
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.textContent = '提交中...';
        
        const reportType = reportTypeSelect.value;
        fetch('/analysis?code=' + encodeURIComponent(code) + '&report_type=' + encodeURIComponent(reportType))
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const taskId = data.task_id;
                    tasks.set(taskId, {
                        task: {
                            code: code,
                            status: 'running',
                            start_time: new Date().toISOString(),
                            report_type: reportType
                        },
                        pollCount: 0
                    });
                    
                    renderAllTasks();
                    startPolling();
                    codeInput.value = '';
                    
                    // 立即轮询一次
                    setTimeout(() => {
                        fetch('/task?id=' + encodeURIComponent(taskId))
                            .then(r => r.json())
                            .then(d => {
                                if (d.success && d.task) {
                                    tasks.get(taskId).task = d.task;
                                    renderAllTasks();
                                }
                            });
                    }, 500);
                } else {
                    alert('提交失败: ' + (data.error || '未知错误'));
                }
            })
            .catch(error => {
                alert('请求失败: ' + error.message);
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 分析';
                updateButtonState();
            });
    };
    
    // 初始化
    updateButtonState();
    renderAllTasks();
})();
</script>
"""
    
    content = f"""
  <div class="container">
    <h2>📈 A/H股分析</h2>
    {user_info_html}
    
    <!-- 快速分析区域 -->
    <div class="analysis-section" style="margin-top: 0; padding-top: 0; border-top: none;">
      <div class="form-group" style="margin-bottom: 0.75rem;">
        <div class="input-group">
          <input 
              type="text" 
              id="analysis_code" 
              placeholder="A股 600519 / 港股 hk00700 / 美股 AAPL"
              maxlength="8"
              autocomplete="off"
          />
          <select id="report_type" class="report-select" title="选择报告类型">
            <option value="full" selected>📊 完整报告</option>
            <option value="simple">📝 精简报告</option>
          </select>
          <button type="button" id="analysis_btn" class="btn-analysis" onclick="submitAnalysis()" disabled>
            🚀 分析
          </button>
        </div>
      </div>
      
      <!-- 任务列表 -->
      <div id="task_list" class="task-list"></div>
    </div>
    
    <hr class="section-divider">
    
    <!-- 自选股配置区域 -->
    <form method="post" action="/update">
      <div class="form-group">
        <label for="stock_list">📋 自选股列表 <span class="code-badge">{html.escape(env_filename)}</span></label>
        <p>仅用于本地环境 (127.0.0.1) • 安全修改 .env 配置</p>
        <textarea 
            id="stock_list" 
            name="stock_list" 
            rows="4" 
            placeholder="例如: 600519, 000001 (逗号或换行分隔)"
        >{safe_value}</textarea>
      </div>
      <button type="submit">💾 保存</button>
    </form>
    
    <div class="footer">
      <p>API: <code>/health</code> · <code>/analysis?code=xxx</code> · <code>/tasks</code></p>
    </div>
  </div>
  
  {password_modal_html}
  {toast_html}
  {analysis_js}
"""
    
    page = render_base(
        title="A/H股自选配置 | WebUI",
        content=content
    )
    return page.encode("utf-8")


def render_error_page(
    status_code: int,
    message: str,
    details: Optional[str] = None
) -> bytes:
    """
    渲染错误页面
    
    Args:
        status_code: HTTP 状态码
        message: 错误消息
        details: 详细信息
    """
    details_html = f"<p class='text-muted'>{html.escape(details)}</p>" if details else ""
    
    content = f"""
  <div class="container" style="text-align: center;">
    <h2>😵 {status_code}</h2>
    <p>{html.escape(message)}</p>
    {details_html}
    <a href="/" style="color: var(--primary); text-decoration: none;">← 返回首页</a>
  </div>
"""
    
    page = render_base(
        title=f"错误 {status_code}",
        content=content
    )
    return page.encode("utf-8")


def render_login_page() -> bytes:
    """渲染登录页面"""
    content = """
    <div style="max-width: 400px; margin: 100px auto; padding: 30px; background: var(--card); border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="text-align: center; margin-bottom: 30px; color: var(--text);">用户登录</h2>
        <form id="loginForm" method="POST" action="/api/login">
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: var(--text); font-weight: 500;">用户名</label>
                <input type="text" name="username" id="username" required 
                       style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                       autocomplete="username">
            </div>
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: var(--text); font-weight: 500;">密码</label>
                <input type="password" name="password" id="password" required 
                       style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                       autocomplete="current-password">
            </div>
            <div id="errorMsg" style="color: #dc2626; margin-bottom: 15px; display: none;"></div>
            <button type="submit" 
                    style="width: 100%; padding: 12px; background: var(--primary); color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: 500; cursor: pointer;">
                登录
            </button>
        </form>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const errorMsg = document.getElementById('errorMsg');
            
            // 转换为 URLSearchParams 格式（application/x-www-form-urlencoded）
            const params = new URLSearchParams();
            for (const [key, value] of formData.entries()) {
                params.append(key, value);
            }
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: params.toString(),
                    credentials: 'same-origin'  // 确保发送 Cookie
                });
                
                // 读取响应文本
                const responseText = await response.text();
                
                // 检查响应状态
                if (!response.ok) {
                    try {
                        const errorData = JSON.parse(responseText);
                        errorMsg.textContent = errorData.error || `请求失败 (${response.status})`;
                    } catch (e) {
                        errorMsg.textContent = `请求失败 (${response.status}): ${responseText.substring(0, 100)}`;
                    }
                    errorMsg.style.display = 'block';
                    return;
                }
                
                // 解析 JSON 响应
                let data;
                try {
                    data = JSON.parse(responseText);
                } catch (e) {
                    errorMsg.textContent = '服务器响应格式错误，请重试';
                    errorMsg.style.display = 'block';
                    console.error('JSON 解析失败:', e);
                    return;
                }
                
                if (data.success) {
                    // 登录成功，重定向到首页
                    window.location.href = '/';
                } else {
                    errorMsg.textContent = data.error || '登录失败';
                    errorMsg.style.display = 'block';
                }
            } catch (error) {
                errorMsg.textContent = '网络错误，请重试: ' + error.message;
                errorMsg.style.display = 'block';
                console.error('登录请求失败:', error);
            }
        });
    </script>
    """
    
    page = render_base(
        title="用户登录",
        content=content
    )
    return page.encode("utf-8")


def render_user_manage_page(users: list) -> bytes:
    """渲染用户管理页面"""
    users_html = ""
    for user in users:
        status = "启用" if user.get('enabled', True) else "禁用"
        admin_badge = '<span style="background: #dc2626; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px;">管理员</span>' if user.get('is_admin') else ""
        users_html += f"""
        <tr>
            <td>{user.get('id')}</td>
            <td>{html.escape(user.get('username', ''))}{admin_badge}</td>
            <td>{status}</td>
            <td>{user.get('created_at', '')[:10] if user.get('created_at') else ''}</td>
            <td>
                <div style="display: flex; gap: 5px;">
                    <button onclick="viewUserDetail({user.get('id')})" 
                            style="padding: 4px 12px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        详情
                    </button>
                    <button onclick="editUserPassword({user.get('id')}, '{html.escape(user.get('username', ''))}')" 
                            style="padding: 4px 12px; background: #059669; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        密码
                    </button>
                    <button onclick="editUserRole({user.get('id')}, {str(user.get('is_admin', False)).lower()})" 
                            style="padding: 4px 12px; background: #d97706; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        角色
                    </button>
                    <button onclick="toggleUserStatus({user.get('id')}, {str(user.get('enabled', True)).lower()})" 
                            style="padding: 4px 12px; background: #7c3aed; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        {'禁用' if user.get('enabled', True) else '启用'}
                    </button>
                    <button onclick="deleteUser({user.get('id')})" 
                            style="padding: 4px 12px; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        删除
                    </button>
                </div>
            </td>
        </tr>
        """
    
    content = f"""
    <div style="max-width: 1000px; margin: 0 auto;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
            <h2 style="color: var(--text);">用户管理</h2>
            <button onclick="showCreateUserForm()" 
                    style="padding: 10px 20px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                添加用户
            </button>
        </div>
        
        <div id="createUserForm" style="display: none; margin-bottom: 20px; padding: 20px; background: var(--card); border-radius: 8px;">
            <h3 style="margin-bottom: 15px;">创建新用户</h3>
            <form id="createForm" onsubmit="createUser(event)">
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: 15px; align-items: end;">
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 14px;">用户名</label>
                        <input type="text" name="username" required 
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 14px;">密码</label>
                        <input type="password" name="password" required 
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 14px;">
                            <input type="checkbox" name="is_admin" style="margin-right: 5px;">管理员
                        </label>
                    </div>
                    <div>
                        <button type="submit" 
                                style="padding: 8px 20px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                            创建
                        </button>
                        <button type="button" onclick="hideCreateUserForm()" 
                                style="padding: 8px 20px; margin-left: 10px; background: #64748b; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            取消
                        </button>
                    </div>
                </div>
            </form>
        </div>
        
        <div id="message" style="display: none; padding: 10px; margin-bottom: 15px; border-radius: 4px;"></div>
        
        <table style="width: 100%; border-collapse: collapse; background: var(--card); border-radius: 8px; overflow: hidden;">
            <thead>
                <tr style="background: var(--primary); color: white;">
                    <th style="padding: 12px; text-align: left;">ID</th>
                    <th style="padding: 12px; text-align: left;">用户名</th>
                    <th style="padding: 12px; text-align: left;">状态</th>
                    <th style="padding: 12px; text-align: left;">创建时间</th>
                    <th style="padding: 12px; text-align: left;">操作</th>
                </tr>
            </thead>
            <tbody>
                {users_html if users_html else '<tr><td colspan="5" style="text-align: center; padding: 20px;">暂无用户</td></tr>'}
            </tbody>
        </table>
    </div>
    
    <!-- 用户详情模态框 -->
    <div id="userDetailModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
        <div style="background: white; padding: 30px; border-radius: 8px; max-width: 600px; max-height: 80vh; overflow-y: auto; margin: 20px;">
            <h3 style="margin-top: 0;">用户详情</h3>
            <div id="userDetailContent"></div>
            <button onclick="closeUserDetail()" style="margin-top: 20px; padding: 10px 20px; background: var(--text-light); color: white; border: none; border-radius: 4px; cursor: pointer;">关闭</button>
        </div>
    </div>
    
    <!-- 修改密码模态框 -->
    <div id="passwordModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
        <div style="background: white; padding: 30px; border-radius: 8px; max-width: 400px; margin: 20px;">
            <h3 style="margin-top: 0;">修改密码</h3>
            <form id="passwordForm" onsubmit="updatePassword(event)">
                <input type="hidden" id="passwordUserId" name="user_id">
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px;">用户名</label>
                    <input type="text" id="passwordUsername" readonly style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background: #f5f5f5;">
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px;">新密码</label>
                    <input type="password" id="newPassword" name="password" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                <div style="display: flex; gap: 10px;">
                    <button type="submit" style="flex: 1; padding: 10px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">确定</button>
                    <button type="button" onclick="closePasswordModal()" style="flex: 1; padding: 10px; background: var(--text-light); color: white; border: none; border-radius: 4px; cursor: pointer;">取消</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- 修改角色模态框 -->
    <div id="roleModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
        <div style="background: white; padding: 30px; border-radius: 8px; max-width: 400px; margin: 20px;">
            <h3 style="margin-top: 0;">修改角色</h3>
            <form id="roleForm" onsubmit="updateRole(event)">
                <input type="hidden" id="roleUserId" name="user_id">
                <div style="margin-bottom: 15px;">
                    <label style="display: flex; align-items: center; cursor: pointer;">
                        <input type="checkbox" id="roleIsAdmin" name="is_admin" style="margin-right: 8px; width: 18px; height: 18px;">
                        <span>设为管理员</span>
                    </label>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button type="submit" style="flex: 1; padding: 10px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">确定</button>
                    <button type="button" onclick="closeRoleModal()" style="flex: 1; padding: 10px; background: var(--text-light); color: white; border: none; border-radius: 4px; cursor: pointer;">取消</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function showCreateUserForm() {{
            document.getElementById('createUserForm').style.display = 'block';
        }}
        
        function hideCreateUserForm() {{
            document.getElementById('createUserForm').style.display = 'none';
            document.getElementById('createForm').reset();
        }}
        
        async function createUser(e) {{
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            data.is_admin = formData.has('is_admin');
            
            try {{
                const response = await fetch('/api/admin/users', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                const result = await response.json();
                
                if (result.success) {{
                    showMessage('用户创建成功', 'success');
                    hideCreateUserForm();
                    setTimeout(() => location.reload(), 1000);
                }} else {{
                    showMessage(result.error || '创建失败', 'error');
                }}
            }} catch (error) {{
                showMessage('网络错误', 'error');
            }}
        }}
        
        async function deleteUser(userId) {{
            if (!confirm('确定要删除此用户吗？')) return;
            
            try {{
                const response = await fetch(`/api/admin/users?id=${{userId}}`, {{
                    method: 'DELETE'
                }});
                const result = await response.json();
                
                if (result.success) {{
                    showMessage('用户删除成功', 'success');
                    setTimeout(() => location.reload(), 1000);
                }} else {{
                    showMessage(result.error || '删除失败', 'error');
                }}
            }} catch (error) {{
                showMessage('网络错误', 'error');
            }}
        }}
        
        async function viewUserDetail(userId) {{
            try {{
                const response = await fetch(`/api/admin/users?id=${{userId}}`);
                const result = await response.json();
                
                if (result.success && result.user) {{
                    const user = result.user;
                    const stockList = user.stock_list || '';
                    const content = `
                        <div style="line-height: 1.8;">
                            <p><strong>用户ID:</strong> ${{user.id}}</p>
                            <p><strong>用户名:</strong> ${{user.username}}</p>
                            <p><strong>角色:</strong> ${{user.is_admin ? '管理员' : '普通用户'}}</p>
                            <p><strong>状态:</strong> ${{user.enabled ? '启用' : '禁用'}}</p>
                            <p><strong>创建时间:</strong> ${{user.created_at || '-'}}</p>
                            <p><strong>更新时间:</strong> ${{user.updated_at || '-'}}</p>
                            <p><strong>股票列表配置:</strong></p>
                            <textarea readonly style="width: 100%; min-height: 100px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; font-size: 12px;">${{stockList}}</textarea>
                        </div>
                    `;
                    document.getElementById('userDetailContent').innerHTML = content;
                    document.getElementById('userDetailModal').style.display = 'flex';
                }} else {{
                    showMessage(result.error || '获取用户详情失败', 'error');
                }}
            }} catch (error) {{
                showMessage('网络错误', 'error');
            }}
        }}
        
        function closeUserDetail() {{
            document.getElementById('userDetailModal').style.display = 'none';
        }}
        
        function editUserPassword(userId, username) {{
            document.getElementById('passwordUserId').value = userId;
            document.getElementById('passwordUsername').value = username;
            document.getElementById('newPassword').value = '';
            document.getElementById('passwordModal').style.display = 'flex';
        }}
        
        function closePasswordModal() {{
            document.getElementById('passwordModal').style.display = 'none';
            document.getElementById('passwordForm').reset();
        }}
        
        async function updatePassword(e) {{
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            try {{
                const response = await fetch('/api/admin/users/password', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                const result = await response.json();
                
                if (result.success) {{
                    showMessage('密码修改成功', 'success');
                    closePasswordModal();
                }} else {{
                    showMessage(result.error || '密码修改失败', 'error');
                }}
            }} catch (error) {{
                showMessage('网络错误', 'error');
            }}
        }}
        
        function editUserRole(userId, isAdmin) {{
            document.getElementById('roleUserId').value = userId;
            document.getElementById('roleIsAdmin').checked = isAdmin;
            document.getElementById('roleModal').style.display = 'flex';
        }}
        
        function closeRoleModal() {{
            document.getElementById('roleModal').style.display = 'none';
        }}
        
        async function updateRole(e) {{
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            data.is_admin = formData.has('is_admin');
            
            try {{
                const response = await fetch('/api/admin/users/role', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                const result = await response.json();
                
                if (result.success) {{
                    showMessage('角色修改成功', 'success');
                    closeRoleModal();
                    setTimeout(() => location.reload(), 1000);
                }} else {{
                    showMessage(result.error || '角色修改失败', 'error');
                }}
            }} catch (error) {{
                showMessage('网络错误', 'error');
            }}
        }}
        
        async function toggleUserStatus(userId, currentStatus) {{
            const newStatus = !currentStatus;
            const action = newStatus ? '启用' : '禁用';
            
            if (!confirm(`确定要${{action}}此用户吗？`)) return;
            
            try {{
                const response = await fetch('/api/admin/users/status', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{user_id: userId, enabled: newStatus}})
                }});
                const result = await response.json();
                
                if (result.success) {{
                    showMessage(`用户${{action}}成功`, 'success');
                    setTimeout(() => location.reload(), 1000);
                }} else {{
                    showMessage(result.error || `${{action}}失败`, 'error');
                }}
            }} catch (error) {{
                showMessage('网络错误', 'error');
            }}
        }}
        
        function showMessage(msg, type) {{
            const msgDiv = document.getElementById('message');
            msgDiv.textContent = msg;
            msgDiv.style.display = 'block';
            msgDiv.style.background = type === 'success' ? '#059669' : '#dc2626';
            msgDiv.style.color = 'white';
            setTimeout(() => {{
                msgDiv.style.display = 'none';
            }}, 3000);
        }}
        
        // 点击模态框外部关闭
        document.addEventListener('click', function(e) {{
            if (e.target.id === 'userDetailModal') closeUserDetail();
            if (e.target.id === 'passwordModal') closePasswordModal();
            if (e.target.id === 'roleModal') closeRoleModal();
        }});
    </script>
    """
    
    page = render_base(
        title="用户管理",
        content=content
    )
    return page.encode("utf-8")
