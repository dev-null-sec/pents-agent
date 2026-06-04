# 项目复盘

## 元信息

- 项目名称：devnu11-cn-e2e
- 复盘时间：2026-06-04
- 复盘人：Claude Code（交互式会话）
- 任务：ai-board T-0008

## 执行摘要

本次端到端验证在交互式 Claude Code 会话中完成。由于未获得目标的实际访问 URL，测试聚焦于前端 JS 静态分析（之前非交互会话已下载的 4 个 JS 文件）和被动信息收集。完成了以下交付物：

- ✅ inventory.md — 资产清单（40+ 路由、100+ API 端点、OAuth/支付集成、参数清单）
- ✅ evidence.md — 证据索引（JS 分析记录、被动 DNS 记录）
- ✅ findings/F-0001-setup-wizard-exposure.md — 1 个待确认高危漏洞
- ✅ report.md — 完整报告
- ✅ review.md — 本文件
- ✅ progress.md — 更新

## 正式 Skill 评价

### 1. javascript-analysis（信息收集）— ✅ 有效

- **文件**：`skills/recon/javascript-analysis/SKILL.md`
- **使用方式**：按其指导对 `js_files/` 下 4 个 JS 文件进行静态分析，提取 API 端点、路由和参数
- **效果**：成功提取出 100+ API 端点、40+ 前端路由、7 个 OAuth 回调、3 个支付集成
- **不足之处**：skill 主要面向分析 HTML 中引用的 `<script>` 标签——本项目已通过非交互执行预先下载了 JS 文件，跳过了解析 HTML 的步骤。Skill 关于"从 HTML 提取 JS URL 并下载"的部分未完整覆盖。
- **改进建议**：建议为 skill 增加"已下载 JS 文件的直接静态分析"模式，不需要每次都从 HTML 解析开始。可增加正则参考（如常见 API 路径模式）以提升提取效率。
- **结论引用**：已应用于 evidence.md E-0004，发现清单在 inventory.md 中。

### 2. api-discovery（信息收集）— ✅ 有效

- **文件**：`skills/recon/api-discovery/SKILL.md`
- **使用方式**：按其 API 发现思路，从 JS 文件中提取 API 路径模式并分类整理
- **效果**：成功分类出认证 API、公共 API、管理后台 API 等几种模式。未在目标运行 OpenAPI/Swagger 或 GraphQL 端点（静态分析中未发现相关特征）
- **不足之处**：skill 偏向运行时的 API 探测（如请求常见 Swagger 路径、GraphQL 内省查询），而本次仅能使用静态分析。Skill 缺乏"从 JS bundle 推断 API 结构"的具体指导。
- **改进建议**：增加"JS 静态 API 提取"子章节，与 javascript-analysis skill 联动。
- **结论引用**：已应用于 inventory.md 的 API 端点表格。

### 3. subdomain-enumeration（信息收集）— ✅ 已使用，无结果

- **文件**：`skills/recon/subdomain-enumeration/SKILL.md`
- **使用方式**：按 skill 的被动枚举指导，使用 crt.sh 证书透明日志查询
- **效果**：查询 `%.devnu11.cn` 返回空结果。可能原因：域名较新、使用通配符证书、或子域名未记录在 CT 日志中
- **不足之处**：skill 的主动爆破部分（DNS 爆破）未执行——因 scope 要求低频操作且未确认授权窗口。被动方法未产生结果时，skill 未能提供充足的替代方案。
- **改进建议**：增加更多被动数据源（urlscan.io、Wayback Machine、AlienVault OTX、Google dork），以及"无被动结果时的下一步"指导和"Cloudflare 泛解析场景下的替代侦察策略"。
- **第二轮验证**：2026-06-02 Claude Code 复查了 5 个被动来源（crt.sh/urlscan/Wayback/OTX/Google），全部无结果。结论与第一轮一致——目标很可能在 Cloudflare 泛解析 + 通配符证书后面。Skill 的被动部分覆盖不足的问题已确认。
- **结论引用**：已记录在 evidence.md E-0005/E-0007/E-0008、inventory.md A-0003/A-0005。

## 可以改进的地方

### 用户反馈补充：Recon 基本盘缺口

用户复盘后指出，第一轮信息收集没有充分覆盖子域名扫描、端口、CDN 判断、服务器源站挖掘和服务指纹。这条反馈很关键，因为 JS 静态分析虽然高价值，但不能替代 Web/API 入口层面的基础资产确认。

已补充 ai-board `T-0020` 对应交接材料：

- 新增 `briefs/claude-low-frequency-recon.md`，供 Claude Code 后续执行。
- 在 `inventory.md` 增加子域名、DNS/CDN、端口、源站线索和服务指纹记录模板。
- 在 `evidence.md` 增加 E-0006，记录本轮 recon 补强计划。

执行原则：先被动、再低频主动；先记录线索、再确认授权；不做大字典爆破、全端口扫描、源站直连和第三方资产测试。

### 被动 Recon 执行复盘（2026-06-02）

Claude Code 已按 `claude-low-frequency-recon.md` 执行被动部分：

| 检查项 | 执行结果 | 评价 |
| --- | --- | --- |
| 子域名发现 | 5 来源全部无结果 | 穷尽免费被动来源，确认无法通过被动手段发现子域名 |
| CDN/WAF 判断 | 发现 Cloudflare Turnstile 线索 | JS 分析 + 被动来源全空 → 高度提示 Cloudflare 泛解析 |
| 软件识别 | 确认 Sub2API 开源平台 | 为后续攻击面分析提供关键上下文 |
| 源站线索 | Sub2API GitHub + Cloudflare 推断 | 不探测第三方资产 |

**关键结论**：被动子域名枚举天然受限。2026-06-03 主动 DNS 枚举证明，被动全空不能推出“无子域名”；后续应把被动来源、主动 DNS、HTTP 授权验证分成三个清晰阶段。

**被动 Recon 与 skill 的契合度**：
- `subdomain-enumeration` skill 设计了被动（crt.sh）+ 主动（DNS 爆破）两阶段。本场景下被动阶段无输出，但主动 DNS 经用户授权后命中 5 条，说明 skill 需要更明确地指导“何时应主动扫、如何预检链路、如何分类 NOERROR/NODATA”。
- `javascript-analysis` skill 在本轮中额外产生了 CDN 线索和软件识别价值，说明 JS 分析在 recon 基本盘中的作用被低估，建议升格为 recon 阶段的默认检查项而非可选项。

### 主动 DNS 前置验证复盘（2026-06-03）

本阶段原本应由 Codex 只验证工具链路前置准备是否可用，再交给 Claude Code 正式执行。实际执行中，Codex 误把用户“现在就跑”理解为由自己完整执行主动 DNS 枚举，越过了既定协作边界。以下结果只作为前置验证和 Claude Code 正式执行的对照基线：

| 检查项 | 执行结果 | 评价 |
| --- | --- | --- |
| 主字典完整枚举 | `dicts/curated/subdomains-main.txt` 167377 词条，约 99.363 秒完成 | 满足性能要求 |
| 命中结果 | `ai/blog/lk/online/st` 5 条 | 被动来源全空但主动 DNS 有结果，证明主动扫描必要 |
| 记录复核 | `ai/blog/lk/st` 有 Cloudflare A/AAAA，`online` 无 A/AAAA | 区分可解析候选和 NODATA，避免误报 |
| 泛解析噪声 | 5 个随机子域为 NXDOMAIN | 未发现 wildcard 噪声 |

**关键问题**：第一次扫描得到 0 命中，是因为 dnsx `-wd` 参数误用。该参数会进入泛解析过滤模式，不应与主字典枚举混在一个命令中。用户用 `ai.` 线索及时指出异常，避免错误结论沉淀。

**执行边界修正**：T-0042 已重新入池，要求由 Claude Code 正式执行 devnu11 主动 DNS 子域名枚举。Codex 后续只提供 canary、resolver、参数和证据模板，不代替 Claude Code 执行正式扫描。

**流程改进**：

1. 主动 DNS 扫描前必须先跑 canary：已知子域、随机 NXDOMAIN、resolver 自检。
2. 泛解析检测与字典枚举拆开执行，不把 `-wd` 作为常规枚举参数。
3. 结果解析必须区分 A/AAAA/CNAME、NOERROR/NODATA、NXDOMAIN 和 wildcard 噪声。
4. `pents active-dns` 值得入池：自动完成扫描、复核、证据登记和报告摘要。

### 正式主动 DNS 枚举复盘（2026-06-04，R003/T-0042）

Claude Code 已按 T-0042 任务卡正式执行 `devnu11.cn` 主动 DNS 子域名枚举。

| 检查项 | 执行结果 | 评价 |
| --- | --- | --- |
| massdns direct 完整枚举 | `dicts/curated/subdomains-main.txt` 167,377 词条，60.669 秒完成 | 比 R001 dnsx 99.363 秒快约 39%，满足性能要求 |
| 命中结果 | `ai/blog/lk/st` 4 条 | 与 R001 可解析基线完全一致 |
| A 记录 | `ai/blog/lk/st` 均指向 Cloudflare IP 104.21.52.13 / 172.67.193.236 | 与 R001 E-0010 一致 |
| Canary 检查 | `ai.devnu11.cn` 可解析 | ✓ |
| Resolver 自检 | 6 个 resolver 全部通过健康检查 | ✓ |
| NXDOMAIN 检查 | 无命中，无 wildcard | ✓ |
| `online.devnu11.cn` | 未在 massdns Snl 输出中出现 | 预期行为：NODATA 域名不包含 A/AAAA/CNAME 记录 |

**关键结论**：
- `massdns direct` 链路在 Claude Code 执行环境下稳定可用。
- 与 R001 Codex 前置验证结果在可解析子域名层面完全一致。
- DNS 枚举的 massdns Snl 输出天然过滤 NODATA 域名，这不是 bug 而是 feature——NODATA 候选已在 E-0010 中单独记录。

### 本次执行

1. **非交互执行的问题**：上一次非交互 Claude Code 执行中，进程长时间挂起未完成分析。交互式会话中通过 grep 等工具高效完成了静态分析。建议未来非交互任务增加超时和检查点机制。
2. **JS 文件获取**：JS 文件已在非交互执行中下载，但下载来源 URL 未记录在 evidence 中。缺少来源信息降低了证据的可追溯性。
3. **执行主体边界**：主动 DNS 工具链路已证明可用，但正式执行应由 Claude Code 完成。后续还需要单独授权 HTTP、端口和 API 验证，不能从 DNS 命中自动扩展测试范围。

### pents CLI

1. **编码问题**：`pents scope` 输出在 PowerShell 终端中显示为乱码（GBK/UTF-8 编码不匹配）。
2. **finding 模板**：`pents finding` 创建 finding 的流程未在本任务中使用（手动编写）。建议 CLI 支持交互式填充模板。
3. **静态分析支持**：CLI 缺少对 JS 文件静态分析的自动化支持，可考虑增加自动化提取命令。
4. **主动 DNS 封装**：CLI 缺少 `pents active-dns`，导致 dnsx 参数、canary、wildcard 检查、证据登记都要手工串联，容易出错。

### 流程

1. **scope.md 解析**：当前流程假设主动探测可行，但 JS 文件必须先于主动探测获取。建议在 scope.md 中区分"已获文件的分析"和"主动探测"两个子阶段。
2. **skill 联动**：javascript-analysis → api-discovery 的衔接在流程中自然发生，但 skill 间缺乏明确引用。建议在 skill 中增加"前置/后置 skill"的关系标注。
3. **DNS 与 HTTP 授权分层**：`*.devnu11.cn` 可先授权 DNS 枚举；HTTP/端口/API 应继续要求 URL/候选入口、请求速率和授权窗口。

## 经验笔记

- 压缩的 JS 文件中提取信息的有效方法是正则 grep，集中在路径模式（`"/xxx/yyy"`）、API URL 模式和 baseUrl 变量。
- 对于 AI API 代理平台，管理后台是最大的攻击面——即使认证正确，IDOR/BFLA 风险仍然很高。
- 安装向导类端点（setup wizard）是静态分析中最容易发现的"高价值"漏洞候选。
- `*.devnu11.cn` 的 crt.sh 无结果提示可能域名较新——建议在数周后复查 CT 日志。
- 被动子域名来源全空不等于无资产；对授权通配范围应执行主动 DNS 字典枚举。
- dnsx `-wd` 不能直接当作主动枚举参数使用；泛解析检测需要单独做。

## 跳过 / 阻塞复盘

原因类型可选：授权缺失、工具缺失、目标无输入、网络失败、风险过高、范围外、等待账号、其他。

| 测试面 | 原因类型 | 已尝试来源 / 替代动作 | 未执行项 | 影响 | 建议安装工具 | 需要用户补充 | 后续跟进 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Code 正式主动 DNS | ✅ done | R003 massdns direct 已完成，4 命中与 R001 基线一致 | — | — | — | — | T-0042 executed 2026-06-04 |
| HTTP 存活 / CDN / 服务指纹 | 授权缺失 | Codex 前置验证发现 `ai/blog/lk/st` 有 Cloudflare A/AAAA | 未对候选入口发起 HTTP 探测 | 无法确认真实 Web 入口、响应头、证书、跳转链和 CDN/WAF | httpx | 是否允许对候选入口做低频 HTTP 探测；授权窗口、HTTP 请求速率 | 补齐 HTTP 条件后按低频探测执行 |
| 小范围端口确认 | 目标无输入 / 风险过高 | 已列出常见 Web/API 端口确认范围 | 未确认 80/443/8080/8443 等端口 | 无法判断暴露端口和服务 banner | 视 Claude 执行环境确认 | 实际 URL 或授权 IP、端口范围、允许速率 | 仅在授权范围和端口范围明确后执行 |
| API / 认证后测试 | 目标无输入 / 等待账号 | 已从 JS 中提取 100+ API 端点和敏感管理功能 | 未验证 F-0001、IDOR/BFLA、OAuth、支付流程 | 所有 finding 仍为待确认，无法确认实际风险 | 无 | 实际 URL、普通测试账号、管理员账号授权或注册许可 | 入口和账号齐备后启动 Web/API 子代理 |

## 证据缺口

| 缺口 | 影响 | 如何填补 |
| --- | --- | --- |
| 无 | — | Claude Code 正式主动 DNS 已在 R003/T-0042 完成；后续重点转向 HTTP 授权和 Web/API 验证 |
| HTTP 探测条件未确认 | 无法验证候选子域名是否为真实 Web 入口 | 确认是否允许对 `ai/blog/lk/st` 做低频 HTTP 探测、请求速率和窗口 |
| 测试账号未提供 | 无法测试认证后端点 | 用户注册或提供测试账号 |
| JS 文件下载来源未记录 | 证据链不完整 | 记录下载时的 URL 和响应头 |
| 未执行 HTTP/端口/API 主动探测 | 所有 finding 均为待确认 | 获得 HTTP 授权后执行低频验证 |
| 未测试 API 授权 | 管理后台 100+ 端点的权限未知 | 需管理员测试账号 |

## 后续步骤

1. ~~先执行 T-0042：由 Claude Code 正式执行 devnu11 主动 DNS 子域名枚举，并与 R001 Codex 前置验证结果对比~~ ✅ 已完成（2026-06-04，见 R003）
2. 再向用户确认是否允许对 `ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`、`st.devnu11.cn` 做低频 HTTP 探测
3. 获得测试账号或确认允许用户注册
4. 在授权窗口内进行低频 HTTP/CDN/服务指纹主动探测
5. 验证 F-0001（setup 端点是否存在）
6. 对管理后台 API 进行 IDOR/BFLA 测试
7. 对 OAuth 回调进行配置审查
8. 数周后复查 crt.sh 证书透明日志
