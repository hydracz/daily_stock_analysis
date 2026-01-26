#!/bin/bash
# ============================================================
# 测试登录 API 脚本
# ============================================================
# 
# 用法：
#   ./test_login_api.sh [username] [password] [host] [port]
#
# 示例：
#   ./test_login_api.sh admin mypassword 127.0.0.1 8000
#   ./test_login_api.sh admin mypassword 0.0.0.0 8000
# ============================================================

# 默认参数
USERNAME="${1:-admin}"
PASSWORD="${2:-test123}"
HOST="${3:-127.0.0.1}"
PORT="${4:-8000}"

# 如果 HOST 是 0.0.0.0，改为 127.0.0.1（curl 不支持 0.0.0.0）
if [ "$HOST" = "0.0.0.0" ]; then
    HOST="127.0.0.1"
    echo "注意: 0.0.0.0 已自动改为 127.0.0.1（curl 不支持 0.0.0.0）"
fi

echo "=========================================="
echo "测试登录 API"
echo "=========================================="
echo "URL: http://${HOST}:${PORT}/api/login"
echo "用户名: ${USERNAME}"
echo "密码: ${PASSWORD:0:3}***"
echo "=========================================="
echo ""

# 发送登录请求
echo "发送请求..."
echo ""

curl -v -X POST \
  "http://${HOST}:${PORT}/api/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Accept: application/json" \
  -H "User-Agent: curl-test-script" \
  -d "username=${USERNAME}&password=${PASSWORD}" \
  -w "\n\n==========================================\nHTTP状态码: %{http_code}\n总时间: %{time_total}s\n响应大小: %{size_download} bytes\n==========================================\n" \
  --connect-timeout 10 \
  --max-time 30

echo ""
echo "测试完成！"
echo ""
echo "预期结果："
echo "  - HTTP 200 状态码"
echo "  - JSON 响应: {\"success\": true, \"message\": \"登录成功\", ...}"
echo "  - 如果失败，会返回错误信息"
