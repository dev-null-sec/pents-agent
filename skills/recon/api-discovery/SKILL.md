---
name: api-discovery
description: 发现目标 API 端点，通过 OpenAPI/Swagger 检测、API 版本枚举和 REST 端点扫描构建完整的 API 攻击面。
category: recon
source: xalgorix
tags:
  - API 发现
  - 信息收集
  - Swagger
  - OpenAPI
required_tools:
  - curl
---

# API 端点发现

## 适用场景

- 渗透测试侦察阶段，需要发现目标的 API 端点。
- 目标可能暴露了 OpenAPI/Swagger 文档但未注意。
- 需要枚举 API 版本和常见 REST 路径。

## 授权边界

- 被动发现 API 路径属于正常侦察范围。
- 发现的 API 端点不直接测试，先记录到 inventory。

## 前置条件

- 目标主域名或已知 Web 服务。
- 常见 API 路径字典。
- 推荐先运行 `javascript-analysis`：如果已经从 JS bundle 提取出 API 路径、base URL、OAuth/支付/管理功能线索，本 skill 应优先整理这些静态结果，再决定是否做低频运行时探测。

## 执行步骤

### 步骤 0：从 JS bundle 推断 API 结构

如果 `javascript-analysis` 已产出 `api_endpoints.txt`、`js_config_hints.txt` 或 inventory 中已有 API 端点，先做静态归类：

```bash
# 按路径前缀粗分 API
grep -E '^/api/|^/v[0-9]/|/admin/|/auth/|/oauth|/payment|/setup' api_endpoints.txt | sort -u > api_from_js.txt

# 提取可能的 base URL 和环境配置
grep -E 'baseURL|baseUrl|apiBase|VITE_|oauth|oidc|stripe|payment|turnstile|captcha' js_config_hints.txt > api_config_from_js.txt
```

归类维度：

- 认证相关：login、logout、register、reset、token、session、captcha。
- 用户侧资源：profile、account、subscription、usage、key、model。
- 管理后台：admin、settings、system、users、billing、audit。
- 集成：OAuth/OIDC、支付、SMTP、对象存储、第三方模型供应商。
- 安装/初始化：setup、install、wizard、bootstrap。

记录要求：

- 静态发现的端点先写入 inventory，状态为“待运行时确认”。
- 如果没有实际 URL、账号或授权窗口，不得主动请求这些端点。
- 敏感管理功能只记录攻击面和待测假设，不声称漏洞已确认。

### 步骤 1：OpenAPI/Swagger 检测

```bash
# 常见文档路径
for path in swagger.json openapi.json api-docs v1/swagger.json \
            api/swagger.json v2/api-docs v3/api-docs api/v1/openapi.json \
            swagger-ui.html docs/api; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://<target>/$path")
  [ "$code" = "200" ] && echo "FOUND: /$path (HTTP $code)"
done
```

### 步骤 2：API 版本枚举

```bash
# 常见版本路径
for v in v1 v2 v3 v4 v5 api/v1 api/v2 api/v3 latest beta alpha; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://<target>/$v/")
  [ "$code" != "404" ] && echo "VERSION: /$v/ (HTTP $code)"
done

# 版本头注入
curl -s "https://<target>/api/" \
  -H "Accept-Version: v1" -H "API-Version: 2" -w "%{http_code}"
```

### 步骤 3：REST 端点枚举

```bash
# 常见 REST 资源
RESOURCES=(
  users user accounts profile posts comments
  orders products settings config admin
  files uploads documents assets images
  search auth login register signup
)

for r in "${RESOURCES[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://<target>/api/$r")
  [ "$code" != "404" ] && echo "RESOURCE: /api/$r (HTTP $code)"
done
```

### 步骤 4：HTTP 方法枚举

```bash
# 对发现的端点测试 HTTP 方法
endpoint="https://<target>/api/users"
for method in GET POST PUT PATCH DELETE OPTIONS HEAD; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$endpoint")
  echo "$method: $code"
done
```

### 步骤 5：GraphQL 探测

```bash
# GraphQL 端点
for path in graphql gql query api/graphql; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST -H "Content-Type: application/json" \
    -d '{"query":"{__typename}"}' "https://<target>/$path")
  [ "$code" = "200" ] && echo "GraphQL: /$path"
done
```

### 步骤 6：Content Negotiation

```bash
# 尝试不同格式
curl -s "https://<target>/api/users" \
  -H "Accept: application/json" -w "JSON: %{http_code}\n" -o /dev/null

curl -s "https://<target>/api/users" \
  -H "Accept: application/xml" -w "XML: %{http_code}\n" -o /dev/null
```

## 停止条件

- 发现暴露的 OpenAPI 文档包含所有端点时，记录文档路径即可，不持续枚举。
- 枚举响应包含敏感数据（如用户列表），停止并记录。
- JS 静态结果已经足够建立 API 攻击面，但缺少实际 URL、账号或授权窗口时，只输出静态推断结果，不进入运行时探测。

## 输出格式

- API 来源：JS 静态推断、OpenAPI/Swagger、版本枚举、REST 探测、GraphQL 探测。
- 从 JS 推断的 API 基础路径、base URL、版本和功能模块。
- OpenAPI/Swagger 文档路径。
- GraphQL 端点。
- REST 资源和 HTTP 方法支持矩阵。
- 所有发现写入 inventory 的 API 端点表。
- 建议下一步：哪些端点需要认证后测试、哪些只需低频确认、哪些必须等待管理员账号或专项授权。

## 验收标准

1. 如果已有 JS bundle 结果，已先完成静态 API 归类，并标注与 `javascript-analysis` 的前后置关系。
2. 如果实际 URL、授权窗口和允许速率已确认，探测了至少 10 种 Swagger/OpenAPI 文档路径。
3. 如果允许运行时枚举，枚举了至少 4 个 API 版本。
4. 如果允许路径探测，探测了至少 15 种常见 REST 资源。
5. 如果允许方法探测，对每个发现的端点测试了 HTTP 方法。
6. 对未执行项写明原因类型、影响和需要用户补充的信息。
