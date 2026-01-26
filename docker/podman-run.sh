#!/bin/bash
# ===================================
# Podman 容器运行脚本
# ===================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "警告: 未找到 .env 文件，请先创建配置文件"
    echo "可以复制 .env.example 作为模板:"
    echo "  cp .env.example .env"
    echo ""
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 运行模式
MODE="${1:-webui}"

case "$MODE" in
    webui)
        CONTAINER_NAME="stock-webui"
        COMMAND="python main.py --webui-only"
        PORT_MAPPING="-p 8000:8000"
        ;;
    analyzer)
        CONTAINER_NAME="stock-analyzer"
        COMMAND="python main.py --schedule"
        PORT_MAPPING=""
        ;;
    *)
        echo "用法: $0 [webui|analyzer]"
        echo ""
        echo "模式说明:"
        echo "  webui     - WebUI 模式，启动 Web 管理界面（默认）"
        echo "  analyzer  - 定时任务模式，每日自动执行分析"
        exit 1
        ;;
esac

echo "=========================================="
echo "启动 Podman 容器: ${CONTAINER_NAME}"
echo "模式: ${MODE}"
echo "=========================================="

# 检查容器是否已存在
if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "检测到已存在的容器: ${CONTAINER_NAME}"
    read -p "是否删除并重新创建？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "停止并删除旧容器..."
        podman stop "${CONTAINER_NAME}" 2>/dev/null || true
        podman rm "${CONTAINER_NAME}" 2>/dev/null || true
    else
        echo "使用现有容器..."
        podman start "${CONTAINER_NAME}"
        echo ""
        echo "查看日志: podman logs -f ${CONTAINER_NAME}"
        exit 0
    fi
fi

# 检查镜像是否存在
IMAGE_NAME="stock-analysis:latest"
if ! podman images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE_NAME}$"; then
    echo "镜像不存在，开始构建..."
    "$SCRIPT_DIR/podman-build.sh"
fi

# 创建必要的目录
mkdir -p data logs reports

# 运行容器
echo "启动容器..."
podman run -d \
    --name "${CONTAINER_NAME}" \
    --env-file .env \
    ${PORT_MAPPING} \
    -v "${PROJECT_ROOT}/data:/app/data" \
    -v "${PROJECT_ROOT}/logs:/app/logs" \
    -v "${PROJECT_ROOT}/reports:/app/reports" \
    -v "${PROJECT_ROOT}/.env:/app/.env" \
    -e TZ=Asia/Shanghai \
    -e WEBUI_HOST=0.0.0.0 \
    -e WEBUI_PORT=8000 \
    "${IMAGE_NAME}" \
    ${COMMAND}

echo ""
echo "=========================================="
echo "容器启动成功！"
echo "=========================================="
echo ""
echo "容器名称: ${CONTAINER_NAME}"
echo "查看日志: podman logs -f ${CONTAINER_NAME}"
echo "查看状态: podman ps | grep ${CONTAINER_NAME}"
echo "停止容器: podman stop ${CONTAINER_NAME}"
echo "删除容器: podman rm ${CONTAINER_NAME}"
if [ "$MODE" = "webui" ]; then
    echo ""
    echo "WebUI 访问地址: http://localhost:8000"
fi
echo ""
