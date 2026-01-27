# Systemd 服务安装指南

本目录包含将 Daily Stock Analysis 安装为 systemd 服务的配置文件和安装脚本。

## 文件说明

- `daily-stock-analysis.service` - systemd 服务配置文件模板
- `install-service.sh` - 自动安装脚本
- `README.md` - 本文件

## 快速安装

### 1. 运行安装脚本

```bash
cd /path/to/daily_stock_analysis
sudo ./systemd/install-service.sh [用户名]
```

如果不指定用户名，脚本会自动使用当前用户（或 `SUDO_USER` 环境变量指定的用户）。

### 2. 安装脚本功能

安装脚本会自动：

1. **检测项目根目录**
   - 从脚本位置推断
   - 检查是否是 git 仓库
   - 从当前工作目录查找
   - 检查常见安装位置（`/opt/daily_stock_analysis`, `~/daily_stock_analysis`）

2. **检测 Python 解释器**
   - 优先使用 `python3`
   - 验证 Python 版本

3. **检测 .env 文件位置**
   - 项目根目录下的 `.env`
   - 用户主目录下的 `.env`
   - `/etc/daily-stock-analysis/.env`
   - 环境变量 `ENV_FILE` 指定的路径

4. **生成 systemd 服务文件**
   - 自动配置工作目录
   - 设置环境变量
   - 配置日志输出
   - 设置安全选项

5. **安装并启动服务**
   - 重新加载 systemd 配置
   - 启用服务（开机自启）
   - 启动服务

## 服务管理

### 查看服务状态

```bash
sudo systemctl status daily-stock-analysis
```

### 查看服务日志

```bash
# 实时查看日志
sudo journalctl -u daily-stock-analysis -f

# 查看最近 100 行日志
sudo journalctl -u daily-stock-analysis -n 100

# 查看今天的日志
sudo journalctl -u daily-stock-analysis --since today
```

### 重启服务

```bash
sudo systemctl restart daily-stock-analysis
```

### 停止服务

```bash
sudo systemctl stop daily-stock-analysis
```

### 禁用服务（取消开机自启）

```bash
sudo systemctl disable daily-stock-analysis
```

### 启用服务（开机自启）

```bash
sudo systemctl enable daily-stock-analysis
```

## 服务配置

### 运行模式

服务默认使用 `--webui-only` 模式，仅启动 WebUI 服务，通过 API 手动触发分析。

如果需要定时任务模式，编辑服务文件：

```bash
sudo systemctl edit daily-stock-analysis
```

或者直接编辑：

```bash
sudo nano /etc/systemd/system/daily-stock-analysis.service
```

修改 `ExecStart` 行：

```ini
# 模式1: 仅 WebUI（默认）
ExecStart=/usr/bin/python3 /path/to/main.py --webui-only

# 模式2: WebUI + 定时任务
ExecStart=/usr/bin/python3 /path/to/main.py --schedule --webui
```

然后重新加载并重启：

```bash
sudo systemctl daemon-reload
sudo systemctl restart daily-stock-analysis
```

### 环境变量

服务会自动加载 `.env` 文件中的环境变量。如果 `.env` 文件位置发生变化，需要更新服务文件：

```bash
sudo systemctl edit daily-stock-analysis
```

添加或修改：

```ini
[Service]
EnvironmentFile=/path/to/.env
```

### 工作目录

服务的工作目录设置为项目根目录，确保相对路径（如日志目录）正常工作。

## 代码更新

当代码仓库更新后，服务会自动使用新的代码（因为工作目录指向项目目录）。

### 更新代码后重启服务

```bash
# 方法1: 重启服务（推荐）
sudo systemctl restart daily-stock-analysis

# 方法2: 重新加载配置（如果只修改了配置）
sudo systemctl daemon-reload
sudo systemctl restart daily-stock-analysis
```

### 自动重启（可选）

如果需要代码更新后自动重启，可以配置 systemd 的路径监控：

```bash
sudo systemctl edit daily-stock-analysis
```

添加：

```ini
[Unit]
PathModified=/path/to/daily_stock_analysis

[Service]
Restart=on-failure
```

## 故障排查

### 服务无法启动

1. 检查服务状态：
   ```bash
   sudo systemctl status daily-stock-analysis
   ```

2. 查看详细日志：
   ```bash
   sudo journalctl -u daily-stock-analysis -n 50 --no-pager
   ```

3. 检查 Python 路径和权限：
   ```bash
   which python3
   ls -la /path/to/daily_stock_analysis/main.py
   ```

4. 检查 .env 文件：
   ```bash
   ls -la /path/to/.env
   cat /path/to/.env  # 确认配置正确
   ```

### 权限问题

如果遇到权限问题，确保：

1. 项目目录对运行用户可读：
   ```bash
   sudo chown -R username:group /path/to/daily_stock_analysis
   sudo chmod -R u+r /path/to/daily_stock_analysis
   ```

2. 日志目录可写：
   ```bash
   sudo chmod -R u+w /path/to/daily_stock_analysis/logs
   ```

3. .env 文件可读：
   ```bash
   sudo chmod 600 /path/to/.env
   sudo chown username:group /path/to/.env
   ```

### 端口占用

如果 WebUI 端口被占用，修改 `.env` 文件：

```bash
WEBUI_PORT=8001
```

然后重启服务。

## 卸载服务

```bash
# 停止服务
sudo systemctl stop daily-stock-analysis

# 禁用服务
sudo systemctl disable daily-stock-analysis

# 删除服务文件
sudo rm /etc/systemd/system/daily-stock-analysis.service

# 重新加载 systemd
sudo systemctl daemon-reload
```

## 注意事项

1. **.env 文件安全**: `.env` 文件包含敏感信息，确保权限设置为 600，只有运行用户可读。

2. **日志管理**: 服务日志通过 systemd journal 管理，可以使用 `journalctl` 查看。项目日志文件保存在 `logs/` 目录。

3. **自动重启**: 服务配置了自动重启策略，如果服务异常退出，systemd 会在 10 秒后自动重启。

4. **资源限制**: 如果需要限制服务资源使用，可以在服务文件中添加：
   ```ini
   [Service]
   MemoryLimit=2G
   CPUQuota=200%
   ```

5. **网络访问**: 确保服务可以访问外部 API（Gemini API、数据源等）。

## 示例

### 完整安装流程

```bash
# 1. 克隆或进入项目目录
cd ~/daily_stock_analysis

# 2. 确保 .env 文件存在
cp .env.example .env
nano .env  # 编辑配置

# 3. 安装服务
sudo ./systemd/install-service.sh

# 4. 检查服务状态
sudo systemctl status daily-stock-analysis

# 5. 查看日志
sudo journalctl -u daily-stock-analysis -f
```

### 更新代码后重启

```bash
# 1. 拉取最新代码
git pull

# 2. 重启服务
sudo systemctl restart daily-stock-analysis

# 3. 验证服务运行
sudo systemctl status daily-stock-analysis
```

## 支持

如果遇到问题，请：

1. 查看服务日志：`sudo journalctl -u daily-stock-analysis -n 100`
2. 检查项目日志：`tail -f logs/stock_analysis_*.log`
3. 提交 Issue 到 GitHub 仓库
