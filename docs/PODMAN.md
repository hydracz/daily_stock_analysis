# 🦫 Podman 部署快速指南

Podman 是 Docker 的替代品，支持 rootless 模式，无需 root 权限即可运行容器，更加安全。

## 📋 目录

- [快速开始](#快速开始)
- [安装 Podman](#安装-podman)
- [使用方式](#使用方式)
- [常用命令](#常用命令)
- [与 Docker 的区别](#与-docker-的区别)
- [常见问题](#常见问题)

## 快速开始

### 1. 安装 Podman

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y podman

# CentOS/RHEL 8+
sudo yum install -y podman

# Fedora
sudo dnf install -y podman

# macOS
brew install podman
podman machine init
podman machine start
```

### 2. 准备项目

```bash
# 克隆仓库
git clone https://github.com/ZhuLinsen/daily_stock_analysis.git
cd daily_stock_analysis

# 配置环境变量
cp .env.example .env
vim .env  # 填入 API Key 和配置
```

### 3. 启动服务

#### 方式一：使用脚本（推荐，最简单）

```bash
# 构建镜像
./docker/podman-build.sh

# 运行 WebUI 模式
./docker/podman-run.sh webui

# 运行定时任务模式
./docker/podman-run.sh analyzer
```

#### 方式二：使用 Podman Compose（Podman 4.0+）

```bash
# 构建并启动 WebUI 模式
podman compose -f ./docker/podman-compose.yml up -d webui

# 构建并启动定时任务模式
podman compose -f ./docker/podman-compose.yml up -d analyzer

# 同时启动两种模式
podman compose -f ./docker/podman-compose.yml up -d
```

#### 方式三：使用 podman-compose（旧版本）

```bash
# 安装 podman-compose
pip install podman-compose

# 构建并启动
podman-compose -f ./docker/podman-compose.yml up -d webui
```

### 4. 访问 WebUI

启动 WebUI 模式后，访问：`http://localhost:8000`

## 使用方式

### 运行模式

| 模式 | 说明 | 端口 | 启动命令 |
|------|------|------|----------|
| WebUI 模式 | 启动 Web 管理界面，手动触发分析 | 8000 | `./docker/podman-run.sh webui` |
| 定时任务模式 | 每日自动执行分析 | - | `./docker/podman-run.sh analyzer` |
| 同时启动 | 同时运行 WebUI 和定时任务 | 8000 | `podman compose -f ./docker/podman-compose.yml up -d` |

## 常用命令

### 查看状态

```bash
# 查看运行中的容器
podman ps

# 查看所有容器（包括已停止）
podman ps -a

# 查看容器状态（使用 compose）
podman compose -f ./docker/podman-compose.yml ps
```

### 查看日志

```bash
# 查看容器日志
podman logs -f stock-webui
podman logs -f stock-analyzer

# 查看日志（使用 compose）
podman compose -f ./docker/podman-compose.yml logs -f webui
```

### 停止和启动

```bash
# 停止容器
podman stop stock-webui
podman stop stock-analyzer

# 启动容器
podman start stock-webui
podman start stock-analyzer

# 停止所有服务（使用 compose）
podman compose -f ./docker/podman-compose.yml down

# 重启服务（使用 compose）
podman compose -f ./docker/podman-compose.yml restart
```

### 进入容器

```bash
# 进入容器执行命令
podman exec -it stock-webui bash

# 在容器内执行 Python 命令
podman exec stock-analyzer python main.py --no-notify
```

### 更新和重建

```bash
# 更新代码
git pull

# 重建镜像（使用脚本）
./docker/podman-build.sh

# 重建镜像（使用 compose）
podman compose -f ./docker/podman-compose.yml build --no-cache

# 重新部署
podman compose -f ./docker/podman-compose.yml up -d webui
```

### 删除容器和镜像

```bash
# 删除容器
podman rm stock-webui stock-analyzer

# 删除镜像
podman rmi stock-analysis:latest

# 清理所有未使用的资源
podman system prune -a
```

## 与 Docker 的区别

| 特性 | Docker | Podman |
|------|--------|--------|
| **权限** | 需要 root 或 docker 组 | 支持 rootless，无需特殊权限 |
| **守护进程** | 需要 dockerd 守护进程 | 无需守护进程，更轻量 |
| **命令兼容性** | - | 大部分命令与 Docker 兼容 |
| **安全性** | 需要 root 权限 | 更安全，支持 rootless |
| **镜像构建** | `docker build` | `podman build` |
| **Compose** | `docker-compose` | `podman compose` 或 `podman-compose` |
| **网络** | `host.docker.internal` | `host.containers.internal` |

### 命令对照表

| Docker 命令 | Podman 命令 |
|-------------|-------------|
| `docker build` | `podman build` |
| `docker run` | `podman run` |
| `docker ps` | `podman ps` |
| `docker logs` | `podman logs` |
| `docker exec` | `podman exec` |
| `docker stop` | `podman stop` |
| `docker rm` | `podman rm` |
| `docker images` | `podman images` |
| `docker-compose` | `podman compose` 或 `podman-compose` |

## 常见问题

### 1. Podman 未安装

**错误信息：** `command not found: podman`

**解决方法：**
```bash
# Ubuntu/Debian
sudo apt-get install -y podman

# CentOS/RHEL
sudo yum install -y podman

# Fedora
sudo dnf install -y podman
```

### 2. podman compose 命令不存在

**错误信息：** `command not found: podman compose`

**解决方法：**

Podman 4.0+ 已内置 `podman compose` 命令。如果使用旧版本，可以：

```bash
# 方式一：升级 Podman 到 4.0+
# 方式二：安装 podman-compose
pip install podman-compose

# 然后使用 podman-compose（注意是连字符）
podman-compose -f ./docker/podman-compose.yml up -d
```

### 3. 权限问题

**错误信息：** `permission denied`

**解决方法：**

Podman 支持 rootless 模式，通常不需要特殊权限。如果遇到权限问题：

```bash
# 检查用户命名空间配置
podman info

# 如果使用 rootless 模式，确保用户命名空间已正确配置
# 某些系统可能需要额外配置，参考 Podman 官方文档
```

### 4. 端口已被占用

**错误信息：** `port is already allocated`

**解决方法：**

```bash
# 检查端口占用
sudo netstat -tulpn | grep 8000
# 或
sudo ss -tulpn | grep 8000

# 停止占用端口的进程，或修改 podman-compose.yml 中的端口映射
```

### 5. 容器无法访问网络

**解决方法：**

```bash
# 检查 Podman 网络
podman network ls

# 重启 Podman 网络
podman network reload

# 如果使用 rootless 模式，可能需要配置网络
podman machine init  # macOS/Windows
```

### 6. 数据目录权限问题

**解决方法：**

```bash
# 确保数据目录存在且有正确权限
mkdir -p data logs reports
chmod 755 data logs reports

# 如果容器内无法写入，检查目录权限
ls -la data logs reports
```

### 7. 镜像构建失败

**解决方法：**

```bash
# 清理构建缓存
podman system prune -a

# 使用 --no-cache 重新构建
podman build --no-cache -f docker/Dockerfile -t stock-analysis:latest .

# 或使用脚本
./docker/podman-build.sh
```

## 更多资源

- [完整部署指南](DEPLOY.md)
- [完整配置指南](full-guide.md)
- [Podman 官方文档](https://podman.io/docs)

---

**提示：** 如果遇到其他问题，请查看 [部署指南](DEPLOY.md) 或提交 [Issue](https://github.com/ZhuLinsen/daily_stock_analysis/issues)。
