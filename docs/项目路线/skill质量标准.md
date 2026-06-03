# 正式 Skill 质量标准

> 本文档定义 `skills/` 正式武器库的入库标准。只有通过质量治理的 skill 才能进入正式武器库。

## 语言标准

- **正式 skill 必须使用简体中文撰写**，确保国内安服人员和 Claude Code 中文会话可直接使用。
- 原始参考资料（`refer/xalgorix/`）保留英文原文，不做全量翻译。
- 命令、工具名、URL、HTTP 方法、参数名等技术标识保持原名。

## 正式 Skill 结构

每个正式 skill 必须是一个独立的 Markdown 文件（`SKILL.md`），放在 `skills/<分类>/<skill名称>/` 下。

### 必需 frontmatter

```yaml
---
name: <kebab-case 名称，与目录名一致>
description: <一句话描述，中文，说明这个 skill 做什么>
category: <分类：recon | web | api | network | privesc | cloud | mobile | iot | redteam | forensics>
tags:
  - <标签1>
  - <标签2>
required_tools:
  - <依赖工具名 或 "无">
---
```

### 必需正文章节

每个正式 skill 必须包含以下章节，不可缺省：

| 章节 | 要求 |
| --- | --- |
| **适用场景** | 什么情况下加载这个 skill。写清楚目标类型、技术栈和应用条件。 |
| **授权边界** | 引用授权范围约束。写明哪些操作用 skill 后仍需主代理确认，哪些在此 skill 范围内可自主执行。 |
| **前置条件** | 需要什么工具、账号、权限、知识准备。 |
| **执行步骤** | 每一步做什么、用什么工具/命令、检查什么。必须可被 Claude Code 逐步执行。 |
| **停止条件** | 什么情况下必须停下来报告主代理。包括：疑似越界、证据不足、响应异常、触发 WAF/IDS。 |
| **输出格式** | 规范输出结构。至少包含被测目标、测试方法、结果摘要、证据引用和建议下一步。 |
| **验收标准** | 用什么指标判断此 skill 已正确执行完毕。 |

### 可选章节

| 章节 | 用途 |
| --- | --- |
| **常见误判** | 容易被误报为漏洞的正常行为。 |
| **绕过技巧** | WAF/过滤绕过的常见变体。 |
| **参考案例** | 真实漏洞案例或靶场复现过程。 |

## 禁止内容

正式 skill 不得包含：

- 破坏性操作或自动化 exploit（除非 skill 本身是"验证漏洞是否存在"且标记为高风险需确认）。
- 范围外目标的测试指令。
- 未经验证的第三方工具安装命令。
- 含糊的"尝试更多 payload"类无限循环指令。

## 质量审查清单

每个正式 skill 入库前必须通过以下检查：

1. [ ] 所有必需章节完整，无占位符残留。
2. [ ] 中文表述清晰，命令和代码示例可复制执行。
3. [ ] 授权边界明确写出。
4. [ ] 停止条件有具体判定标准（不是"遇到异常就停"这种废话）。
5. [ ] 输出格式可被 `pents merge` 或主代理直接引用。
6. [ ] 至少在一个靶场或真实授权测试中验证可用。

## 分类规范

| 分类目录 | 覆盖范围 | 示例 |
| --- | --- | --- |
| `skills/recon/` | 子域名枚举、JS 分析、API 发现、技术栈指纹、端口扫描 | subdomain-enumeration、js-analysis |
| `skills/web/` | XSS、SQLi、CSRF、SSRF、SSTI、XXE、文件上传、目录遍历、JWT、CORS | xss-reflected、sqli-error-based、file-upload-bypass |
| `skills/api/` | BOLA、BFLA、mass-assignment、GraphQL、OAuth 绕过、JWT 攻击 | bola-id-enumeration、graphql-introspection |
| `skills/network/` | 内网扫描、ARP 欺骗、DNS 隧道、SMB 漏洞检测 | smb-enumeration、dns-zone-transfer |
| `skills/privesc/` | 提权、持久化、横向移动（仅限授权范围内验证） | linux-privesc-enum、kerberoasting |
| `skills/cloud/` | S3 桶检测、IAM 权限、云凭证泄露 | s3-bucket-enum、iam-policy-check |
| `skills/mobile/` | APK 分析、移动 API 代理 | apk-static-analysis |
| `skills/iot/` | 固件分析、OT/ICS 协议 | firmware-extraction |
| `skills/redteam/` | C2 基础设施、钓鱼检测规避、内网横向 | cobalt-strike-setup |
| `skills/forensics/` | 日志分析、内存取证、时间线重建 | log-analysis-webserver |

## 入库流程

1. 从 `refer/xalgorix/internal/tools/skills/data/` 或实战经验中挑选候选。
2. 按本文档结构重写或治理。
3. 通过质量审查清单 6 项检查。
4. 放入 `skills/<分类>/<skill名称>/SKILL.md`。
5. 更新 `skills/README.md` 中的 skill 清单表。
