---
name: oauth-misconfiguration
description: 检测 OAuth 2.0 / OpenID Connect 实现中的配置缺陷，包括 redirect_uri 绕过、CSRF、PKCE 绕过和 scope 越权。
category: web
source: xalgorix
tags:
  - OAuth
  - OpenID Connect
  - 认证缺陷
  - 授权码拦截
required_tools:
  - curl
---

# OAuth 配置缺陷检测

## 适用场景

- 目标应用使用 OAuth 2.0 或 OpenID Connect 进行第三方登录。
- 需要测试 redirect_uri 验证是否严格。
- 检查 PKCE 和 state 参数是否正确实现。

## 授权边界

- **OAuth 测试可能触发向外部服务器的重定向。** 使用 Interactsh 或 Burp Collaborator 作为测试回调地址。
- 不利用发现的漏洞接管其他用户账户，仅用测试账号验证。
- 不窃取真实用户的授权码或 Token。

## 前置条件

- 目标支持 OAuth 登录。
- Interactsh 或 Burp Collaborator 用于接收重定向。

## 执行步骤

### 步骤 1：OAuth 流程侦察

```bash
# 发起登录，抓取授权请求
# 记录以下参数：
# - client_id
# - redirect_uri
# - response_type (code / token / id_token)
# - scope
# - state (是否一致)
# - code_challenge / code_challenge_method (PKCE)
```

### 步骤 2：redirect_uri 绕过

```bash
# 尝试 19 种常见绕过
INTERACT="https://<your_interactsh_server>"

# 开放重定向
curl -v "https://<idp>/authorize?client_id=xxx&redirect_uri=https://<target>/callback?next=$INTERACT&response_type=code"

# 子域名劫持
curl -v "https://<idp>/authorize?...&redirect_uri=https://<target>.attacker.com/callback..."

# 路径穿越
curl -v "https://<idp>/authorize?...&redirect_uri=https://<target>/../attacker/callback..."

# @ 符号混淆
curl -v "https://<idp>/authorize?...&redirect_uri=https://<target>@$INTERACT/callback..."

# 注册参数污染
curl -v "https://<idp>/authorize?...&redirect_uri=https://<target>/callback&redirect_uri=$INTERACT"
```

### 步骤 3：State 参数 CSRF 测试

```bash
# 检查 state 是否被验证
# 发起授权请求时省略 state 参数
curl -v "https://<idp>/authorize?client_id=xxx&redirect_uri=https://<target>/callback&response_type=code&scope=openid"

# 如果授权成功且未报 "missing state" 错误，存在 CSRF 风险
```

### 步骤 4：PKCE 绕过

```bash
# 检查 code_challenge 是否被验证
# 1. 创建 code_verifier 和 code_challenge
# 2. 发起请求缺失 code_challenge
# 3. 回调时提供 code_verifier，观察是否被要求验证

# 降级攻击：尝试使用 plain 方法
curl -v "https://<idp>/authorize?...&code_challenge=unhashed&code_challenge_method=plain"
```

### 步骤 5：Scope 越权

```bash
# 尝试添加超出注册范围的 scope
curl -v "https://<idp>/authorize?...&scope=openid+profile+email+admin+offline_access"

# 如果授权页面显示请求了额外 scope 且可以批准，存在 scope 越权
```

## 停止条件

- redirect_uri 可被指向攻击者控制的域名时，记录为严重漏洞并停止。
- 不要用发现的漏洞获取其他用户的授权码或 Token。

## 输出格式

- OAuth 提供商和流程类型（Authorization Code / Implicit / PKCE）。
- redirect_uri 绕过成功的方法。
- CSRF 和 PKCE 保护状态。
- Scope 越权可能性。

## 验收标准

1. 测试了至少 5 种 redirect_uri 绕过方法。
2. 检查了 state 参数和 PKCE 验证。
3. 测试了 scope 越权。
4. 所有测试使用 Interactsh 而非个人服务器。
