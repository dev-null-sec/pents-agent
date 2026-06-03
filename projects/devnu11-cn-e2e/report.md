# 渗透测试报告

## 元数据

- 项目：devnu11-cn-e2e
- 目标：`*.devnu11.cn`
- 报告日期：2026-06-03
- 测试者：Claude Code (AI-assisted)
- 范围文件：scope.md

## 执行摘要

本次端到端验证（ai-board T-0008 及后续 recon 补充）对目标 `*.devnu11.cn` 执行了授权渗透测试的信息收集和静态分析阶段。已完成前端 JS 文件静态分析、被动信息收集和一次主动 DNS 子域名字典枚举；尚未进行 HTTP 存活探测、主动端口探测、服务指纹探测或漏洞验证请求。

**关键发现：**

- 目标是一个 AI API 代理/中转平台（SPA），前端技术栈为 Vue 3.5.26 + Axios + Vue i18n
- 通过 JS 静态分析和公开资料确认软件为 Sub2API 开源 AI API 代理平台
- 通过 JS 静态分析识别出 40+ 前端路由、100+ API 端点、7 个 OAuth 集成、3 个支付集成
- 5 个被动来源（crt.sh、urlscan.io、Wayback Machine、AlienVault OTX、Google 搜索）均未发现子域名或 URL 记录
- 主动 DNS 主字典枚举命中 5 个 DNS 名称：`ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`、`online.devnu11.cn`、`st.devnu11.cn`
- `ai/blog/lk/st` 指向 Cloudflare A/AAAA；`online` 为 NOERROR 但无 A/AAAA，暂记为 NODATA 候选
- 发现 Cloudflare Turnstile 集成线索，较可能存在 Cloudflare 泛解析或通配符证书场景
- 发现 **1 个待确认高危漏洞**：安装向导端点暴露（F-0001）
- 发现多个需进一步验证的敏感功能：系统重启/回滚、SMTP 测试、Admin API Key 重置等
- 被动子域名枚举（crt.sh）未返回结果

**限制：** 本次测试仅完成静态分析、被动 recon 和 DNS 枚举；未发起 HTTP、端口、路径/API 或漏洞验证请求。完整的安全评估需要：HTTP 探测授权窗口、请求速率、测试账号、以及对候选入口的低频主动验证许可。

## 测试范围

| 类型 | 目标 | 备注 |
| --- | --- | --- |
| web/api | `*.devnu11.cn` | 用户声明自有域名和服务器，允许授权测试 |
| 静态分析 | 前端 JS 文件 (js_files/) | 已下载的 4 个 JS 文件 |
| 被动 DNS / URL 来源 | crt.sh、urlscan.io、Wayback Machine、AlienVault OTX、Google 搜索 | 5 个来源均无子域名或 URL 记录 |
| 主动 DNS 枚举 | `devnu11.cn` 子域名字典枚举 | 使用 `dicts/curated/subdomains-main.txt`，167377 词条 |

## 测试方法

1. **范围审阅** — 读取 scope.md，确认授权范围和禁止动作 ✓
2. **被动信息收集** — crt.sh、urlscan.io、Wayback Machine、AlienVault OTX、Google 搜索均无结果 ✓
3. **JS 静态分析** — 使用 `skills/recon/javascript-analysis/SKILL.md` 分析 4 个前端 JS 文件 ✓
4. **API 发现** — 使用 `skills/recon/api-discovery/SKILL.md` 提取 API 端点和参数 ✓
5. **子域名枚举** — 被动枚举 5 个来源均无结果；主动 DNS 主字典命中 5 条 ✓
6. **Web 表面测试** — 未执行（需目标实际 URL）
7. **API 测试** — 未执行（需目标实际 URL + 测试账号）
8. **认证与会话测试** — 未执行（需测试账号）
9. **证据整理** — 完成 evidence.md ✓
10. **报告编写** — 本文件 ✓

## 执行状态与限制

原因类型可选：授权缺失、工具缺失、目标无输入、网络失败、风险过高、范围外、等待账号、其他。

| 测试面 | 状态 | 原因类型 | 已尝试来源 / 替代动作 | 未执行项 | 影响 | 需要用户补充 |
| --- | --- | --- | --- | --- | --- | --- |
| 被动信息收集 | done |  | crt.sh、urlscan、Wayback、OTX、Google |  | 5 个来源均无子域名或 URL 记录 | 无 |
| JS 静态分析 | done |  | 已分析 4 个前端 JS 文件 |  | 已提取路由、API、参数、OAuth、支付和敏感管理功能 | 无 |
| 主动 DNS 子域名枚举 | done |  | dnsx + `dicts/curated/subdomains-main.txt` 完整扫描；E-0009/E-0010 |  | 命中 5 个 DNS 名称，其中 4 个有 Cloudflare A/AAAA | 无 |
| HTTP 存活 / CDN / 服务指纹 | blocker | 授权缺失 | 已获得 `ai/blog/lk/st` 候选 DNS 名称和 Cloudflare A/AAAA 线索 | 未对候选入口发起 HTTP 探测 | 无法确认真实入口、响应头、证书、跳转链和 CDN/WAF | 是否允许低频 HTTP 探测、授权窗口、HTTP 请求速率 |
| 端口确认 | blocker | 目标无输入 / 风险过高 | 已记录小范围端口确认清单 | 未扫描端口 | 无法确认 Web/API 常见端口暴露 | 实际 URL 或授权 IP、端口范围、允许速率 |
| API / 认证后测试 | blocker | 目标无输入 / 等待账号 | 已从 JS 提取 100+ API 端点 | 未验证 F-0001、IDOR/BFLA、OAuth、支付流程 | 所有漏洞仍为待确认 | 实际 URL、普通测试账号、管理员账号授权或注册许可 |

## 漏洞汇总

| 编号 | 标题 | 严重程度 | 状态 |
| --- | --- | --- | --- |
| F-0001 | 安装向导端点暴露 | 高 (7.5) | 待确认 |

## 详细漏洞

见 [findings/F-0001-setup-wizard-exposure.md](findings/F-0001-setup-wizard-exposure.md)。

## 信息收集成果

### 应用识别

目标是一个 AI API 代理/中转平台，具备完整的前后端功能：
- 用户注册/登录/密码重置（邮箱 + 6 种 OAuth）
- API Key 管理与用量统计
- 订阅与支付（Stripe、Airwallex、二维码支付）
- 兑换码/推广联盟系统
- 功能丰富的管理后台（100+ API 端点）

第二轮被动 recon 进一步识别目标软件为 **Sub2API**。公开资料显示其后端技术栈包括 Go、PostgreSQL 和 Redis；这些信息仅用于理解攻击面，未对第三方 GitHub 仓库或官方 demo 站执行测试。

### 被动 Recon 结论

- 5 个被动来源均无 `devnu11.cn` 子域名或 URL 记录。
- JS 中存在 Cloudflare Turnstile 配置字段，结合被动来源全空，提示常规被动来源覆盖不足。

### 主动 DNS 结论

- 2026-06-03 已执行主动 DNS 主字典枚举，167377 词条约 99.363 秒完成。
- 命中 `ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`、`online.devnu11.cn`、`st.devnu11.cn`。
- `ai/blog/lk/st` 指向同一组 Cloudflare A/AAAA；`online` 为 NOERROR 但无 A/AAAA，暂不作为 Web 入口。
- 上一次 0 命中是 dnsx `-wd` 参数误用导致的扫描链路问题，已在 R001 复盘中记录。
- 在未确认 HTTP 授权窗口和请求速率前，不应对候选子域名执行 HTTP 探测、端口扫描或源站直连。

### OAuth 集成

7 个 OAuth/OIDC 集成方，涵盖用户登录和管理后台账号绑定：
- LinuxDo、微信、微信支付、钉钉、通用 OIDC（用户侧）
- Gemini OAuth、Antigravity OAuth（管理后台账号绑定）

### 敏感功能

管理后台包含多个高风险功能，需确认权限控制：
- 系统重启（`/admin/system/restart`）
- 系统更新/回滚（`/admin/system/update`, `/admin/system/rollback`）
- Admin API Key 重新生成（`/admin/settings/admin-api-key/regenerate`）
- SMTP 测试（`/admin/settings/test-smtp`）
- 账号批量操作（`/admin/accounts/batch*`）

## 风险主题

1. **安装向导残留** — setup 端点若生产环境未禁用，是最严重风险，可能导致完整系统接管
2. **攻击面广阔** — 100+ 管理 API 端点，即使管理后台已鉴权，内部授权缺陷（IDOR/BFLA）风险较高
3. **OAuth 配置** — 7 个 OAuth 集成，每个都可能存在 redirect_uri 绕过、state 参数缺失等配置缺陷
4. **支付安全** — 3 个支付集成，需确认价格参数在服务端校验

## 修复建议

1. **立即**：确认生产环境 `/api/v1/setup/*` 端点已禁用
2. **短期**：审查管理后台 API 的认证和授权机制，确认不存在 IDOR/BFLA
3. **中期**：审查所有 OAuth 集成的 redirect_uri 校验；审查支付流程中的价格参数服务端校验
4. **长期**：建议对管理后台进行完整的渗透测试（需测试账号）

## 后续建议

需在获得以下信息后继续：
- 目标实际 URL（例如 `https://xxx.devnu11.cn`）
- 是否允许对 `ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`、`st.devnu11.cn` 执行低频 HTTP 探测
- 授权窗口和允许请求速率，用于低频 HTTP/CDN、端口和服务指纹确认
- 测试账号（普通用户 + 管理员，或由用户注册），用于后续 API 授权、OAuth 和支付流程验证

## 附录

- 资产清单：[inventory.md](inventory.md)
- 测试进度：[progress.md](progress.md)
- 证据索引：[evidence.md](evidence.md)
- 漏洞记录：[findings/F-0001-setup-wizard-exposure.md](findings/F-0001-setup-wizard-exposure.md)
- 项目复盘：[review.md](review.md)
- Skill 清单：[skills/README.md](../../skills/README.md)
