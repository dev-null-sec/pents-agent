---
name: javascript-analysis
description: 分析目标网站的 JavaScript 文件，提取 API 端点、硬编码密钥、Token 和敏感信息。
category: recon
source: xalgorix
tags:
  - 信息收集
  - JavaScript
  - API 发现
  - 密钥泄露
required_tools:
  - curl
  - grep
---

# JavaScript 分析

## 适用场景

- 目标使用了大量前端 JS 框架（React/Vue/Angular），API 交互逻辑在客户端。
- 需要从 JS 中提取隐藏的 API 端点、内部路径和管理功能。
- 检查是否存在硬编码的 API Key、Token、密码或云服务凭证。

## 授权边界

- 只分析可通过浏览器正常访问的 JS 文件，不使用调试器附加或逆向工程。
- 提取到的 API 端点和凭证不能用于越权访问，测试前需主代理确认 scope 覆盖。

## 前置条件

- 已通过子域名枚举和存活探测获得目标 Web 服务列表，或已经拿到可分析的本地 JS 文件。
- 可访问目标网站的页面和 JS 资源；如果只拿到历史下载的 JS 文件，也可以直接进入“已下载 JS 直接分析模式”。
- 可选：`waybackurls` 或 gau 用于提取历史 JS URL。

## 执行步骤

### 步骤 0：已下载 JS 直接分析模式

如果项目目录里已经有 `js_files/`、浏览器缓存、构建产物或上轮 Claude 下载的 JS 文件，不要强行从 HTML 重新开始。先记录来源缺口，再直接分析现有文件：

```bash
find js_files -type f -name "*.js" | sort > js_files_list.txt
wc -l js_files_list.txt
```

记录要求：

- 现有 JS 文件数量、文件名、大小和 hash。
- 下载来源 URL 是否已知；未知时在 evidence/review 里标为证据链缺口。
- 是否存在 `.map`、chunk 文件、i18n、runtime、vendor、admin 等明显模块。

### 步骤 1：收集 JS 文件 URL

从目标页面和 Wayback Machine 提取 JS 文件地址。

```bash
# 从主页提取 script 标签中的 JS
curl -s https://<target.com> | grep -oP 'src="[^"]+\.js"' | cut -d'"' -f2 | sort -u > js_urls.txt

# 从 Wayback Machine 获取历史 JS 文件
echo "<target.com>" | waybackurls | grep '\.js$' | sort -u >> js_urls.txt
```

**预期输出**：`js_urls.txt`，包含所有可访问的 JS 文件 URL。

### 步骤 2：下载 JS 文件

```bash
mkdir -p js_files
while read url; do
  curl -s "$url" -o "js_files/$(basename "$url")" 2>/dev/null
done < js_urls.txt
```

**预期输出**：`js_files/` 目录，包含所有下载的 JS 文件。

### 步骤 3：提取 API 端点

```bash
# 搜索常见 API 路径模式
grep -rhoP '["'\''](/api/v?\d?/[^"'\'' ]+|/graphql|/v\d/[^"'\'' ]+)' js_files/ | sort -u > api_endpoints.txt

# 搜索 fetch/axios 调用
grep -rhoP '(fetch|axios\.(get|post|put|delete))\s*\(\s*["'\''][^"'\'' ]+' js_files/ | sort -u >> api_endpoints.txt
```

**预期输出**：`api_endpoints.txt`，包含从 JS 中提取的 API 路径。

### 步骤 4：搜索密钥和 Token

```bash
# 高置信度模式
grep -rnoP '(api[_-]?key|access[_-]?token|secret|password|private[_-]?key|bearer)\s*[:=]\s*["'\''][^"'\'' ]{8,}' js_files/ > secrets_found.txt

# 低置信度模式（需要人工确认）
grep -rnoP '[A-Za-z0-9+/]{40,}={0,2}' js_files/ | grep -v 'sha256\|base64' >> secrets_low_confidence.txt
```

**预期输出**：`secrets_found.txt` 和 `secrets_low_confidence.txt`。

### 步骤 5：软件识别与配置变量提取

从 JS bundle 中提取应用类型、框架、版本、base URL、功能开关、OAuth/支付/CDN/WAF 线索：

```bash
# 前端框架、HTTP 客户端、常见组件库
grep -rhoP '(Vue|React|Angular|axios|fetch|i18n|pinia|vue-router|vite)' js_files/ | sort -u > js_tech_hints.txt

# API base URL、环境变量、功能开关
grep -rnoP '(baseURL|baseUrl|apiBase|VITE_[A-Z0-9_]+|NODE_ENV|turnstile|captcha|cloudflare|stripe|oauth|oidc|sso)' js_files/ > js_config_hints.txt

# 软件名、版本、版权或开源项目线索
grep -rnoP '(version|Version|copyright|license|github|Sub2API|OneAPI|New API|ChatGPT|OpenAI)' js_files/ > js_software_hints.txt
```

记录要求：

- 软件识别只能写“确认/较可能/线索”，不要仅凭一个字符串过度断言。
- Cloudflare Turnstile、`CF-`、captcha、WAF 相关字段应作为 CDN/WAF 线索写入 inventory/review。
- OAuth、支付、SMTP、系统重启、回滚、Admin API Key 等高敏功能应交给 `api-discovery` 继续整理，不直接测试。

### 步骤 6：Source Map 分析（如有）

```bash
# 检查是否存在 source map 引用
grep -r 'sourceMappingURL' js_files/ | while read line; do
  map_url=$(echo "$line" | grep -oP '//# sourceMappingURL=\K.*')
  curl -s "$map_url" -o "js_files/$(basename "$map_url")" 2>/dev/null
done
```

**预期输出**：下载的 `.map` 文件，可反编译混淆代码。

## 停止条件

- 发现的密钥/Token 疑似生产环境凭证时，立即停止分析并报告主代理，不要自行验证。
- JS 文件超过 500 个时暂停，向主代理报告数量并确认是否继续。
- 发现疑似后门、恶意脚本或非正常注入时记录并报告。

## 输出格式

- API 端点列表（`api_endpoints.txt`），写入 inventory 的 API 端点表。
- 发现的密钥/Token（`secrets_found.txt`），仅摘要报告，不将原始凭证写入 progress。
- 软件识别、配置变量、CDN/WAF、OAuth/支付/管理功能线索。
- Source map 发现（如有）。
- 建议下一步：把 API 端点、base URL、敏感功能和集成线索交给 `api-discovery` 归类；把 CDN/WAF 线索交给 `subdomain-enumeration` 或服务指纹任务验证。

## 验收标准

1. 至少收集并下载目标主要页面引用的 JS 文件。
2. 至少用 3 种正则模式搜索 API 端点和密钥。
3. 发现结果已记录到 inventory 或 progress。
4. 可疑密钥已报告主代理并标记为高风险。
