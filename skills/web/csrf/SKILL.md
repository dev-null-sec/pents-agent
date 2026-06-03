---
name: csrf
description: 检测跨站请求伪造（CSRF）漏洞，验证关键操作是否具备有效的反 CSRF 保护。
category: web
source: xalgorix
tags:
  - CSRF
  - 会话安全
  - 表单安全
  - OWASP Top 10
required_tools:
  - curl
---

# CSRF 跨站请求伪造检测

## 适用场景

- 目标应用有状态变更操作（修改密码、转账、修改邮箱、删除数据）。
- 需要验证这些操作是否受 CSRF Token、SameSite Cookie 或自定义请求头的保护。
- 测试 Cookie 的 SameSite 属性是否有效。

## 授权边界

- **CSRF 测试可能触发实际的状态变更**（如修改密码、删除资源）。使用测试账号和测试数据，不影响真实用户。
- 如果发现 CSRF 漏洞，仅验证 PoC 可行，不利用它修改其他用户数据。

## 前置条件

- 至少一个测试账号。
- 已识别所有涉及状态变更的操作和对应的请求。
- 浏览器环境用于生成 CSRF PoC 页面（可选）。

## 执行步骤

### 步骤 1：识别目标操作

```bash
# 列出所有状态变更操作
# - 修改密码：POST /change-password
# - 修改邮箱：POST /settings/email
# - 转账：POST /transfer
# - 删除资源：DELETE /api/resource/123
# - 修改角色：PUT /api/users/123/role
```

### 步骤 2：检查 CSRF 保护

对每个操作检查保护机制：

```bash
# 正常请求（带 CSRF Token）
curl -v -X POST "https://<target>/change-password" \
  -H "Cookie: session=<token>" \
  -d "csrf_token=<token>&new_password=test123"
```

检查点：
- 请求是否包含 CSRF Token（通常在 body 或自定义头中）。
- 服务端是否验证 Token。
- Token 是否绑定到用户会话。

### 步骤 3：移除 CSRF Token 测试

```bash
# 发送不含 CSRF Token 的请求
curl -X POST "https://<target>/change-password" \
  -H "Cookie: session=<token>" \
  -d "new_password=test123"
```

如果请求成功（非 403/CSRF 错误），记录为 CSRF 漏洞。

### 步骤 4：Token 验证绕过

```bash
# 测试 Token 是否可被替换
# 使用一个有效但属于其他操作或过期的 Token
curl -X POST "https://<target>/change-password" \
  -H "Cookie: session=<token>" \
  -d "csrf_token=invalid_or_expired_token&new_password=test123"

# 测试是否完全移除 Token 字段即可绕过
curl -X POST "https://<target>/change-password" \
  -H "Cookie: session=<token>" \
  -d "new_password=test123"
```

### 步骤 5：SameSite Cookie 检查

```bash
# 检查关键 Cookie 的 SameSite 属性
curl -sI "https://<target>/" | grep -i 'set-cookie'

# SameSite 可能值：
# Strict — 完全阻止跨站请求发送 Cookie
# Lax — 允许 GET 导航请求发送 Cookie（默认）
# None — 允许所有跨站请求（需要 Secure）
# 未设置 — 浏览器行为因版本而异
```

### 步骤 6：Content-Type 绕过

```bash
# 尝试用 text/plain 绕过预检（preflight）
curl -X POST "https://<target>/change-password" \
  -H "Cookie: session=<token>" \
  -H "Content-Type: text/plain" \
  -d '{"new_password":"test123"}'

# 尝试 application/x-www-form-urlencoded
curl -X POST "https://<target>/change-password" \
  -H "Cookie: session=<token>" \
  -d "new_password=test123"
```

## 停止条件

- 发现可导致账户接管（修改密码/邮箱）的 CSRF 漏洞，立即记录并报告，不进一步利用。
- 如果所有操作均有强健的 CSRF Token + SameSite=Strict，记录结论即可。

## 输出格式

- 受保护和不保护的操作列表。
- 保护机制分析（CSRF Token、SameSite、自定义头）。
- 绕过成功的操作及方法。
- SameSite Cookie 配置评估。

## 验收标准

1. 至少测试了 3 种状态变更操作（修改密码、修改信息、删除资源）。
2. 对每个操作测试了有/无 CSRF Token 两种情况。
3. 检查了会话 Cookie 的 SameSite 属性。
4. 如发现漏洞，生成了 PoC 请求。
