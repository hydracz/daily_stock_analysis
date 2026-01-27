#!/bin/bash
# -*- coding: utf-8 -*-
# ============================================================
# Daily Stock Analysis Systemd Service Installer
# ============================================================
#
# 功能：
# 1. 自动检测项目目录和 Python 解释器
# 2. 检测 .env 文件位置
# 3. 生成并安装 systemd 服务文件
# 4. 配置服务自动启动
#
# 使用方法：
#   sudo ./systemd/install-service.sh [用户名]
#
# 如果不指定用户名，将使用当前用户
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检测项目根目录
detect_project_root() {
    # 方法1: 从脚本位置推断
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    
    # 方法2: 检查是否是 git 仓库根目录
    if [ -d "$PROJECT_ROOT/.git" ] || [ -f "$PROJECT_ROOT/main.py" ]; then
        echo "$PROJECT_ROOT"
        return
    fi
    
    # 方法3: 从当前工作目录查找
    CURRENT_DIR="$(pwd)"
    if [ -f "$CURRENT_DIR/main.py" ]; then
        echo "$CURRENT_DIR"
        return
    fi
    
    # 方法4: 尝试查找 daily_stock_analysis 目录
    if [ -d "/opt/daily_stock_analysis" ] && [ -f "/opt/daily_stock_analysis/main.py" ]; then
        echo "/opt/daily_stock_analysis"
        return
    fi
    
    if [ -d "$HOME/daily_stock_analysis" ] && [ -f "$HOME/daily_stock_analysis/main.py" ]; then
        echo "$HOME/daily_stock_analysis"
        return
    fi
    
    error "无法检测项目根目录，请手动指定"
    exit 1
}

# 检测 Python 解释器
detect_python() {
    local python_cmd=""
    
    # 优先级: python3 > python
    if command -v python3 &> /dev/null; then
        python_cmd=$(which python3)
    elif command -v python &> /dev/null; then
        python_cmd=$(which python)
    else
        error "未找到 Python 解释器，请先安装 Python 3" >&2
        exit 1
    fi
    
    # 验证 Python 版本（输出到标准错误，避免被捕获）
    local python_version=$($python_cmd --version 2>&1 | awk '{print $2}')
    # 将信息输出到 stderr，避免被命令替换捕获
    info "检测到 Python: $python_cmd (版本: $python_version)" >&2
    
    # 只输出 Python 路径到标准输出（用于命令替换）
    echo "$python_cmd"
}

# 检测 .env 文件位置
detect_env_file() {
    local project_root=$1
    
    # 优先级: 项目根目录 > 用户主目录 > /etc
    if [ -f "$project_root/.env" ]; then
        echo "$project_root/.env"
        return
    fi
    
    if [ -f "$HOME/.env" ]; then
        echo "$HOME/.env"
        return
    fi
    
    if [ -f "/etc/daily-stock-analysis/.env" ]; then
        echo "/etc/daily-stock-analysis/.env"
        return
    fi
    
    # 检查环境变量 ENV_FILE
    if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
        echo "$ENV_FILE"
        return
    fi
    
    warn ".env 文件未找到，服务将使用系统环境变量"
    echo ""
}

# 获取用户信息
get_user_info() {
    local username=$1
    
    if [ -z "$username" ]; then
        # 如果没有指定用户名，尝试从环境变量获取
        if [ -n "$SUDO_USER" ]; then
            username="$SUDO_USER"
        else
            username=$(whoami)
        fi
    fi
    
    # 验证用户存在
    if ! id "$username" &> /dev/null; then
        error "用户 $username 不存在"
        exit 1
    fi
    
    # 获取用户主目录和组
    USER_HOME=$(eval echo ~$username)
    USER_GROUP=$(id -gn "$username")
    
    echo "$username|$USER_HOME|$USER_GROUP"
}

# 生成 systemd 服务文件
generate_service_file() {
    local project_root=$1
    local python_cmd=$2
    local env_file=$3
    local username=$4
    local user_home=$5
    local service_name="daily-stock-analysis"
    
    local service_file="/etc/systemd/system/${service_name}.service"
    
    info "生成 systemd 服务文件: $service_file"
    
    cat > "$service_file" <<EOF
[Unit]
Description=Daily Stock Analysis Service
After=network.target

[Service]
Type=simple
User=$username
Group=$USER_GROUP
WorkingDirectory=$project_root
Environment="PATH=$user_home/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
EOF

    # 添加 .env 文件（如果存在）
    if [ -n "$env_file" ] && [ -f "$env_file" ]; then
        echo "EnvironmentFile=$env_file" >> "$service_file"
        info "使用环境变量文件: $env_file"
    else
        warn ".env 文件未找到，服务将使用系统环境变量"
    fi
    
    # 添加启动命令
    cat >> "$service_file" <<EOF

# 启动命令
# 模式1: 仅 WebUI 模式（推荐，通过 API 手动触发分析）
ExecStart=$python_cmd $project_root/main.py --webui-only

# 模式2: WebUI + 定时任务模式（取消注释以启用）
# ExecStart=$python_cmd $project_root/main.py --schedule --webui

# 停止命令（优雅关闭）
ExecStop=/bin/kill -SIGTERM \$MAINPID
TimeoutStopSec=30

# 重启策略
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=daily-stock-analysis

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$project_root/logs
ReadWritePaths=$project_root

[Install]
WantedBy=multi-user.target
EOF

    info "服务文件生成完成"
}

# 设置文件权限
set_permissions() {
    local project_root=$1
    local username=$2
    
    info "设置文件权限..."
    
    # 确保项目目录可读
    chown -R "$username:$USER_GROUP" "$project_root"
    chmod -R u+r "$project_root"
    
    # 确保日志目录可写
    if [ -d "$project_root/logs" ]; then
        chmod -R u+w "$project_root/logs"
    else
        mkdir -p "$project_root/logs"
        chown "$username:$USER_GROUP" "$project_root/logs"
        chmod 755 "$project_root/logs"
    fi
    
    # 确保 .env 文件可读（如果存在）
    if [ -f "$project_root/.env" ]; then
        chmod 600 "$project_root/.env"
        chown "$username:$USER_GROUP" "$project_root/.env"
    fi
}

# 安装服务
install_service() {
    local service_name="daily-stock-analysis"
    
    info "重新加载 systemd 配置..."
    systemctl daemon-reload
    
    info "启用服务..."
    systemctl enable "$service_name.service"
    
    info "启动服务..."
    if systemctl start "$service_name.service"; then
        info "服务启动成功"
    else
        error "服务启动失败，请检查日志: journalctl -u $service_name -n 50"
        exit 1
    fi
}

# 显示服务状态
show_status() {
    local service_name="daily-stock-analysis"
    
    echo ""
    info "=== 服务状态 ==="
    systemctl status "$service_name.service" --no-pager -l || true
    
    echo ""
    info "=== 常用命令 ==="
    echo "  查看服务状态: sudo systemctl status $service_name"
    echo "  查看服务日志: sudo journalctl -u $service_name -f"
    echo "  重启服务:     sudo systemctl restart $service_name"
    echo "  停止服务:     sudo systemctl stop $service_name"
    echo "  禁用服务:     sudo systemctl disable $service_name"
    echo ""
}

# 主函数
main() {
    info "=========================================="
    info "Daily Stock Analysis Service Installer"
    info "=========================================="
    echo ""
    
    # 检查 root 权限
    check_root
    
    # 获取用户名（如果指定）
    TARGET_USER="${1:-}"
    
    # 检测项目根目录
    info "检测项目根目录..."
    PROJECT_ROOT=$(detect_project_root)
    info "项目根目录: $PROJECT_ROOT"
    
    # 检测 Python 解释器
    info "检测 Python 解释器..."
    # 将 info 输出重定向到 stderr，只捕获 Python 路径
    PYTHON_CMD=$(detect_python)
    
    # 检测 .env 文件
    info "检测 .env 文件..."
    ENV_FILE=$(detect_env_file "$PROJECT_ROOT")
    if [ -n "$ENV_FILE" ]; then
        info ".env 文件位置: $ENV_FILE"
    fi
    
    # 获取用户信息
    info "获取用户信息..."
    USER_INFO=$(get_user_info "$TARGET_USER")
    IFS='|' read -r USERNAME USER_HOME USER_GROUP <<< "$USER_INFO"
    info "运行用户: $USERNAME"
    info "用户主目录: $USER_HOME"
    info "用户组: $USER_GROUP"
    
    echo ""
    info "=== 安装配置 ==="
    echo "  项目目录: $PROJECT_ROOT"
    echo "  Python:   $PYTHON_CMD"
    echo "  用户:     $USERNAME"
    echo "  .env:     ${ENV_FILE:-未找到}"
    echo ""
    
    read -p "确认安装? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "安装已取消"
        exit 0
    fi
    
    # 生成服务文件
    generate_service_file "$PROJECT_ROOT" "$PYTHON_CMD" "$ENV_FILE" "$USERNAME" "$USER_HOME"
    
    # 设置权限
    set_permissions "$PROJECT_ROOT" "$USERNAME"
    
    # 安装服务
    install_service
    
    # 显示状态
    show_status
    
    info "安装完成！"
}

# 运行主函数
main "$@"
