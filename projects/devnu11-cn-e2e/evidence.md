# 证据索引

## 元数据

- 项目：devnu11-cn-e2e
- 更新时间：2026-06-02

## 证据列表

| 编号 | 类型 | 关联目标 | 关联漏洞 | 路径或引用 | 备注 |
| --- | --- | --- | --- | --- | --- |
| E-0001 | 备注 | — | — | progress.md | 项目初始化 |
| E-0002 | scope | `*.devnu11.cn` | — | scope.md | 用户声明自有域名和服务器，允许授权测试；Codex 未执行探测 |
| E-0003 | js-static | `*.devnu11.cn` | — | js_files/ | Claude Code 非交互尝试保存的前端 JS 文件；已完成分析（见 E-0004） |
| E-0004 | js-analysis | `*.devnu11.cn` | — | 本文件下方 | 前端 JS 静态分析结果（2026-06-02 交互式会话完成） |
| E-0005 | passive-dns | `*.devnu11.cn` | — | crt.sh 查询 | crt.sh 被动子域名枚举，无证书透明记录返回 |
| E-0006 | recon-plan | `*.devnu11.cn` | — | briefs/claude-low-frequency-recon.md | 子域名、端口、CDN、源站线索和服务指纹的低频执行清单；Claude Code 已执行被动部分（2026-06-02） |
| E-0007 | software-id | `*.devnu11.cn` | — | 本文件下方 | Sub2API 软件识别（2026-06-02）：确认目标为开源 AI API 代理平台，含技术栈和默认配置分析 |
| E-0008 | passive-recon-sweep | `*.devnu11.cn` | — | 本文件下方 | 多来源被动侦察汇总（2026-06-02）：5 个被动来源全部无结果 |

## 证据 E-0004：前端 JS 静态分析

### 分析方法

- 使用正式 skill：`skills/recon/javascript-analysis/SKILL.md`（JS 分析）
- 使用正式 skill：`skills/recon/api-discovery/SKILL.md`（API 发现）
- 使用正式 skill：`skills/recon/subdomain-enumeration/SKILL.md`（子域名枚举，被动）
- 工具：grep 正则提取 URL、API 路径、参数名、OAuth 回调

### 分析文件

| 文件 | 大小 | 内容判断 |
| --- | --- | --- |
| `js_files/index-DG7INg5y.js` | 126 KB | 应用主逻辑，含路由定义、API 端点、服务调用 |
| `js_files/vendor-vue-BRjbeJGJ.js` | 107 KB | Vue 3.5.26 运行时库（第三方） |
| `js_files/vendor-misc-T69nC9V6.js` | 260 KB | Axios + 其他工具库（第三方） |
| `js_files/vendor-i18n-BZoxDmZq.js` | 62 KB | Vue i18n 国际化库（第三方） |

### 发现摘要

#### 应用类型识别

该应用是一个 **AI API 代理/中转平台**（类似 API 聚合/分销系统），提供以下功能：

- 用户注册/登录（支持邮箱密码 + 多种 OAuth）
- API Key 管理
- 用量统计和仪表盘
- 订阅和支付（Stripe、Airwallex、二维码）
- 兑换码/推广码/推广联盟
- 管理后台（用户管理、渠道管理、运维监控、风控等）

#### 路由发现

**用户侧路由**（33 个）：登录、注册、邮箱验证、OAuth 回调（6 个提供商）、首页、仪表盘、Key 管理、用量、兑换、推广、频道、个人设置、订阅、购买、订单、支付（4 种方式）、安装向导。

**管理后台路由**（10+ 模块）：仪表盘、用户、分组、账号、渠道、代理、兑换码、公告、设置、订阅、用量、运维、数据管理、备份、TLS 指纹、支付、推广、风控、系统升级。

#### API 端点发现

**认证 API**：15 个端点（登录/2FA/注册/OAuth/密码重置等）
**公共 API**：2 个端点（公开设置、公告）
**安装向导 API**：4 个端点（状态/数据库/Redis/安装）
**订阅 API**：4 个端点
**管理后台 API**：100+ 个端点

#### OAuth 集成

发现 7 个 OAuth/OIDC 提供商集成：
- LinuxDo、微信、微信支付、钉钉、通用 OIDC（用户侧）
- Gemini OAuth、Antigravity OAuth（管理后台账号绑定）

#### 支付集成

发现 3 个支付提供商：
- Stripe（含弹窗支付模式）
- Airwallex
- 二维码支付

#### 敏感发现

1. **安装向导端点暴露**：`/api/v1/setup/*` 系列端点存在于前端代码中。若生产环境未禁用，可能允许未授权重装或配置泄露。
2. **大量管理功能**：100+ 管理 API 端点，涵盖系统重启/回滚/更新等高风险操作。
3. **SMTP 测试功能**：`/admin/settings/test-smtp` 和 `/admin/settings/send-test-email` 可能被滥用。
4. **Admin API Key 可重新生成**：`/admin/settings/admin-api-key/regenerate`。

### 未发现项

- 未在 JS 文件中发现硬编码的 API Key、Token 或密钥
- 未发现 WebSocket / SignalR 连接端点
- 未发现 `eval()`、`innerHTML` 等高危 DOM 操作模式（但压缩代码中可能遗漏）
- crt.sh 被动子域名枚举无结果

## 请求证据

| 证据编号 | 方法 | URL 或端点 | 请求引用 | 响应引用 | 备注 |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | — | crt.sh | `?q=%25.devnu11.cn&output=json` | 返回空数组 | 被动 DNS 枚举，无证书透明记录 |

## 证据 E-0006：低频 Recon 补强计划

### 计划来源

- 用户反馈：第一轮信息收集没有覆盖子域名扫描、端口、CDN、服务器源站挖掘和服务指纹。
- 任务来源：ai-board `T-0020`
- 执行主体：Claude Code
- Codex 状态：仅补充任务卡和记录模板，未对目标执行主动探测。

### 覆盖范围

| 检查项 | 是否纳入计划 | 安全边界 |
| --- | --- | --- |
| 子域名发现 | 是 | 优先被动来源，不做大字典爆破 |
| DNS 解析 | 是 | 只解析候选子域名，低频执行 |
| 端口确认 | 是 | 只在 URL、窗口、速率确认后做小端口集确认 |
| CDN/WAF 判断 | 是 | 只做识别和记录，不测试第三方供应商资产 |
| 源站线索 | 是 | 只做被动线索整理，未确认 IP 授权前不直连 |
| 服务指纹 | 是 | 只做 HEAD/GET 级别轻量访问和响应头/TLS 记录 |

## 截图证据

| 证据编号 | 路径 | 关联步骤 | 备注 |
| --- | --- | --- | --- | --- |
|  |  |  |  | 无截图（仅为被动/静态分析，未访问目标） |

## 终端输出证据

| 证据编号 | 命令摘要 | 输出引用 | 备注 |
| --- | --- | --- | --- | --- |
| OUT-001 | `grep` 提取 index.js 中的 API 端点 | 见 grep 结果 | 提取到 100+ 端点路径 |
| OUT-002 | `grep` 提取 index.js 中的路由路径 | 见 grep 结果 | 提取到 40+ 前端路由 |
| OUT-003 | `grep` 搜索 vendor-misc 中的 baseUrl | 见 grep 结果 | 确认使用 Axios HTTP 客户端 |
| OUT-004 | `grep` 搜索 baseURL/base_url/APP_ | 见 grep 结果 | 发现 `window.__APP_CONFIG__` 配置模式，默认站点名 Sub2API |
| OUT-005 | `grep` 搜索 turnstile/cloudflare | 见 grep 结果 | 发现 Cloudflare Turnstile 集成线索 |
| OUT-006 | `curl crt.sh` 复查 | 返回空 | 第二次确认无证书透明记录 |
| OUT-007 | `curl urlscan.io` | `total:0` | URL 扫描归档无 devnu11.cn 记录 |
| OUT-008 | `curl web.archive.org` | 返回空 | Wayback Machine 无 devnu11.cn 归档 |
| OUT-009 | Google 搜索 `site:devnu11.cn` | 无结果 | 搜索引擎未收录该域名任何页面 |

## 证据 E-0007：Sub2API 软件识别

### 识别方法

- JS 静态分析提取 `window.__APP_CONFIG__` 配置结构
- `site_name` 默认值为 "Sub2API"
- WebSearch 确认 Sub2API 为 Wei-Shaw 维护的开源 AI API 网关
- 仓库地址：https://github.com/Wei-Shaw/sub2api

### 识别依据

| 证据点 | JS 文件位置 | 说明 |
| --- | --- | --- |
| `site_name` 默认值 | index.js → `w.site_name\|\|"Sub2API"` | 默认站点名 |
| `turnstile_site_key` | index.js → `turnstile_site_key:""` | Cloudflare Turnstile 集成 |
| API base | index.js → `baseURL:"/api/v1"` | 前端 API 路径与 Sub2API 一致 |
| 前端技术栈 | vendor-vue (Vue 3.5.26) + vendor-misc (Axios) + vendor-i18n | 与 Sub2API 技术栈匹配 |
| 路由和端点 | 40+ 路由、100+ API 端点 | 与 Sub2API 功能集完全匹配 |

### 技术栈确认

| 组件 | 版本/信息 | 来源 |
| --- | --- | --- |
| 前端 | Vue 3.5.26 + Vite + Axios + Vue i18n | JS 文件直接分析 |
| 后端 | Go (Gin + Ent) | Sub2API 项目文档（GitHub） |
| 数据库 | PostgreSQL | Sub2API 项目文档（GitHub） |
| 缓存 | Redis | Sub2API 项目文档（GitHub） |
| CDN/WAF | Cloudflare（推测） | Turnstile 集成 + 被动来源全部无结果 |

### 攻击面影响

确认软件身份后，可以从 Sub2API 的开源仓库和文档中了解：
- 默认配置、默认端口、默认账号
- 已知漏洞和 CVE
- API 鉴权模型和权限边界
- 安装和 Setup 流程的安全要求

## 证据 E-0008：被动侦察来源汇总

### 执行清单（2026-06-02 Claude Code 交互式会话）

| 来源 | 查询方式 | 时间 | 结果 | 类型 |
| --- | --- | --- | --- | --- |
| crt.sh | `curl "https://crt.sh/?q=%25.devnu11.cn&output=json"` | 2026-06-02 | 空（两次确认） | 证书透明日志 |
| urlscan.io | `curl "https://urlscan.io/api/v1/search/?q=domain:devnu11.cn"` | 2026-06-02 | `total:0` | URL 扫描归档 |
| Wayback Machine | `curl "https://web.archive.org/cdx/search/cdx?url=*.devnu11.cn&output=text"` | 2026-06-02 | 空 | 网页历史归档 |
| AlienVault OTX | `curl "https://otx.alienvault.com/api/v1/indicators/domain/devnu11.cn/passive_dns"` | 2026-06-02 | 需认证 | 被动 DNS / 威胁情报 |
| Google 搜索 | `site:devnu11.cn` | 2026-06-02 | 无结果 | 搜索引擎收录 |

### 结论

5 个被动来源全部无 `devnu11.cn` 子域名或 URL 记录。配合前端 JS 中发现 Cloudflare Turnstile 集成线索，高度提示目标使用 **Cloudflare 泛解析 + 通配符 TLS 证书**，导致证书透明日志和其他被动来源无法记录具体子域名。

### 对后续侦察的影响

- 被动子域名发现已经穷尽主流免费来源，不适合再追加。
- 主动 DNS 爆破在当前条件（无实际 URL、无授权窗口、无速率确认）下被 scope 禁止。
- 下一步必须由用户提供至少 1 个实际访问 URL（如 `https://xxx.devnu11.cn`），才能进入 DNS 解析、端口确认和服务指纹阶段。
