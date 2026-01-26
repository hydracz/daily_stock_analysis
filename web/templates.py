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
        if (status === 'running') { statusIcon = '<span class="spinner"></span>'; statusText = '分析中'; }
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
            detailHtml = '<div class="task-detail" id="detail_' + taskId + '">' +
                '<div class="task-detail-row"><span class="label">趋势</span><span>' + (result.trend_prediction || '-') + '</span></div>' +
                (result.analysis_summary ? '<div class="task-detail-summary">' + result.analysis_summary.substring(0, 100) + '...</div>' : '') +
                '</div>';
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
            <option value="simple">📝 精简报告</option>
            <option value="full">📊 完整报告</option>
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
                    body: params.toString()
                });
                
                // 先读取响应文本（只能读取一次）
                let responseText;
                try {
                    responseText = await response.text();
                    console.log('登录响应状态:', response.status, response.statusText);
                    console.log('登录响应文本:', responseText);
                } catch (e) {
                    errorMsg.textContent = '读取响应失败: ' + e.message;
                    errorMsg.style.display = 'block';
                    console.error('读取响应失败:', e);
                    return;
                }
                
                // 检查响应状态
                if (!response.ok) {
                    // 尝试解析错误信息
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
                    console.log('登录响应数据:', data);
                } catch (e) {
                    errorMsg.textContent = '服务器响应格式错误，请重试';
                    errorMsg.style.display = 'block';
                    console.error('JSON 解析失败:', e, '响应文本:', responseText);
                    return;
                }
                
                if (data.success) {
                    // 登录成功，延迟一下再重定向，确保响应完全处理
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 100);
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
                <button onclick="deleteUser({user.get('id')})" 
                        style="padding: 4px 12px; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                    删除
                </button>
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
    </script>
    """
    
    page = render_base(
        title="用户管理",
        content=content
    )
    return page.encode("utf-8")
