#!/bin/bash
# ===================================
# Podman 镜像构建脚本
# ===================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "构建 Podman 镜像"
echo "=========================================="

# 检查 Podman 是否安装
if ! command -v podman &> /dev/null; then
    echo "错误: 未找到 podman 命令，请先安装 Podman"
    echo ""
    echo "安装方法:"
    echo "  Ubuntu/Debian: sudo apt-get install podman"
    echo "  CentOS/RHEL:   sudo yum install podman"
    echo "  Fedora:        sudo dnf install podman"
    echo "  macOS:         brew install podman"
    exit 1
fi

# 镜像名称
IMAGE_NAME="stock-analysis"
IMAGE_TAG="${1:-latest}"

echo "镜像名称: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "构建上下文: ${PROJECT_ROOT}"
echo ""

# 构建镜像
echo "开始构建镜像..."
podman build \
    -f docker/Dockerfile \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    .

echo ""
echo "=========================================="
echo "构建完成！"
echo "=========================================="
echo ""
echo "查看镜像:"
echo "  podman images ${IMAGE_NAME}"
echo ""
echo "运行容器示例:"
echo "  podman run -d --env-file .env -p 8000:8000 \\"
echo "    -v ./data:/app/data \\"
echo "    -v ./logs:/app/logs \\"
echo "    -v ./reports:/app/reports \\"
echo "    --name stock-webui \\"
echo "    ${IMAGE_NAME}:${IMAGE_TAG} python main.py --webui-only"
echo ""
