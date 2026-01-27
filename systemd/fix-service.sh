#!/bin/bash
# 快速修复脚本 - 清理旧服务并重新安装

set -e

echo "正在清理旧服务..."
sudo systemctl stop daily-stock-analysis 2>/dev/null || true
sudo systemctl disable daily-stock-analysis 2>/dev/null || true
sudo rm -f /etc/systemd/system/daily-stock-analysis.service
sudo systemctl daemon-reload

echo "清理完成，正在重新安装..."
cd "$(dirname "$0")/.."
sudo ./systemd/install-service.sh
