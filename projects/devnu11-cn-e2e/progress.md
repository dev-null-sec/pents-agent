# 测试进度

## 概要

- 项目名称：devnu11-cn-e2e
- 当前阶段：静态分析、被动 recon 和 Claude Code 正式主动 DNS 已完成；HTTP/CDN、端口、服务指纹和漏洞验证等待授权窗口、速率和账号
- 更新时间：2026-06-04

## 时间线

| 时间 | 执行者 | 动作 | 结果 |
| --- | --- | --- | --- |
| 2026-06-02 | Codex | 项目初始化 | 已创建 scope/inventory/evidence/briefs/findings 结构 |
| 2026-06-02 | Codex | 记录授权范围和交接材料 | 未对目标执行任何探测；等待 Claude Code 执行 T-0008 |
| 2026-06-02 | Claude Code | 非交互执行尝试 | 已保存 4 个前端 JS 文件到 `js_files/`，但进程长时间无输出且未更新 progress/inventory/report，Codex 已停止该进程；T-0008 未完成 |
| 2026-06-02 | Claude Code | 交互式继续 T-0008 | 完成 JS 静态分析（4 个文件），被动子域名枚举（crt.sh，无结果），提取 40+ 路由 100+ API 端点；更新 inventory/evidence/report/review；创建 F-0001 候选 finding；T-0008 完成 |
| 2026-06-02 | Codex | 补齐主动验证前置条件记录 | 已在 scope.md 明确实际访问 URL、授权窗口、允许请求速率、测试账号和管理员账号均需在主动探测前确认；Codex 未对目标执行探测 |
| 2026-06-02 | Codex | 补强 recon 基本盘交接材料 | 已新增 Claude 低频 recon 任务卡，并在 inventory/evidence 中补充子域名、端口、CDN、源站线索和服务指纹记录模板；Codex 未对目标执行探测 |
| 2026-06-02 | Claude Code | 低频 recon 被动部分 | 5 个被动来源复查（crt.sh/urlscan/Wayback/OTX/Google）全部无结果；识别软件为 Sub2API；发现 Cloudflare Turnstile 线索；更新 inventory/evidence/progress/review |
| 2026-06-03 | Codex | 主动 DNS 工具链路前置验证 | 执行边界误判，实际跑完 dnsx 主字典；结果只作为前置验证和对照基线，不作为 Claude Code 正式执行验收 |
| 2026-06-04 | Claude Code | T-0042 正式主动 DNS 枚举（massdns direct） | 167377 候选，4 命中（ai/blog/lk/st），60.669 秒；与 R001 可解析基线完全一致 |

## 资产变更

- 已记录授权目标：`*.devnu11.cn`
- 通过 JS 静态分析识别：AI API 代理/中转平台（Vue 3.5.26 SPA）
- 识别 40+ 前端路由、100+ API 端点、7 个 OAuth 集成、3 个支付集成
- Codex 前置验证中误执行完整主动 DNS，命中 5 个名称：`ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`、`online.devnu11.cn`、`st.devnu11.cn`
- 其中 `ai/blog/lk/st` 有 Cloudflare A/AAAA 记录；`online` 为 NOERROR 但无 A/AAAA，暂记为 NODATA 候选

## 已执行测试

| 目标 | 测试面 | 方法 | 结果 | 证据引用 |
| --- | --- | --- | --- | --- |
| `*.devnu11.cn` | scope 准备 | 本地文档记录 | 未执行探测 | E-0002 |
| `*.devnu11.cn` | JS 静态资源 | Claude Code 非交互尝试 | 下载了前端 JS 文件，但未完成分析和报告 | E-0003 |
| `*.devnu11.cn` | JS 静态分析 | grep 正则提取（交互式会话） | 完成分析，提取路由/API/参数/OAuth/支付信息 | E-0004 |
| `*.devnu11.cn` | 被动 DNS | crt.sh 证书透明查询 | 无证书透明记录返回 | E-0005 |
| `*.devnu11.cn` | 正式 skill 验证 | 调用 3 个 recon skill | 全部有效，细节见 review.md | — |
| `*.devnu11.cn` | 主动 DNS 工具链路前置验证 | Codex 使用 dnsx + `dicts/curated/subdomains-main.txt` | 误执行完整扫描；167377 词条约 99.363 秒，命中 `ai/blog/lk/online/st`，仅作 Claude Code 正式执行对照 | E-0009 |
| `ai/blog/lk/online/st.devnu11.cn` | DNS 记录复核 | dnsx A/AAAA/CNAME 查询 | `ai/blog/lk/st` 有 Cloudflare A/AAAA；`online` 为 NODATA 候选 | E-0010 |

## 待执行 Recon 检查

| 目标 | 测试面 | 前置条件 | 执行主体 | 状态 | 记录要求 |
| --- | --- | --- | --- | --- | --- |
| `*.devnu11.cn` | 被动子域名发现 | 被动来源复查 | Claude Code | ✅ done | 5 来源均无结果，记录于 inventory 和 E-0007/E-0008 |
| `*.devnu11.cn` | 主动 DNS 子域名枚举 | T-0042；Claude Code 正式执行 | Claude Code | ✅ done | R003 massdns direct，4 命中与 R001 基线一致；见 E-0011 |
| `*.devnu11.cn` | 软件识别 | JS 静态分析 + WebSearch | Claude Code | ✅ done | 确认 Sub2API 开源平台，记录于 A-0004, E-0007 |
| 候选子域名 | HTTP / CDN 判断 | 需要 HTTP 授权窗口和请求速率 | Claude Code | ⛔ blocker | 已有候选 DNS 名称，但本轮未授权 HTTP 探测 |
| 待确认入口 URL | 端口确认 | 需要 URL、授权窗口、允许速率 | Claude Code | ⛔ blocker | scope.md 前置条件未满足 |
| 待确认入口 URL | 服务指纹 | 需要 URL、授权窗口、允许速率 | Claude Code | ⛔ blocker | scope.md 前置条件未满足 |
| 源站线索 | 源站挖掘 | 只做被动线索；直连 IP 需用户单独授权 | Claude Code | ✅ 被动完成 | 记录 Cloudflare/Su2API 源站线索，见 inventory |

## 跳过 / 阻塞项

原因类型可选：授权缺失、工具缺失、目标无输入、网络失败、风险过高、范围外、等待账号、其他。

| 目标 | 测试面 | 状态 | 原因类型 | 具体原因 | 已尝试来源 / 替代动作 | 影响 | 建议安装工具 | 需要用户补充 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 候选子域名 | HTTP 存活 / CDN / 服务指纹 | blocker | 授权缺失 | 已发现 `ai/blog/lk/st` 有 Cloudflare A/AAAA，但本轮授权只覆盖 DNS 枚举 | 已完成主动 DNS 和 DNS 记录复核 | 无法确认真实 Web 入口、响应头、证书、跳转链和 CDN/WAF | httpx | 是否允许对候选子域名做低频 HTTP 探测；HTTP 请求速率和窗口 |
| 待确认入口 URL | HTTP 存活 / CDN / 服务指纹 | blocker | 目标无输入 / 授权缺失 | 尚未提供实际访问 URL，HTTP 低频速率也未确认 | 已完成 JS 静态分析、软件识别和被动来源复查 | 无法确认真实入口、响应头、证书、跳转链和 CDN/WAF 判断 | httpx | 至少 1 个实际 URL、授权窗口、HTTP 请求速率 |
| 待确认入口 URL | 小范围端口确认 | blocker | 目标无输入 / 风险过高 | 尚未提供实际入口和端口范围，不能凭通配域名扫描 | 已记录端口确认清单和禁止全端口扫描边界 | 无法确认 80/443/8080/8443 等入口暴露情况 | 视 Claude 执行环境确认 | 实际 URL 或授权 IP、授权窗口、端口范围、允许速率 |
| 待确认入口 URL | API / 认证后测试 | blocker | 目标无输入 / 等待账号 | 尚未提供实际 URL、普通测试账号和管理员账号授权 | 已从 JS 提取 100+ API 端点和敏感管理功能 | 无法验证 F-0001、IDOR/BFLA、OAuth、支付流程 | 无 | 实际 URL、测试账号、管理员账号授权或注册许可 |

## 候选漏洞

| 编号 | 标题 | 状态 | 证据引用 |
| --- | --- | --- | --- |
| F-0001 | 安装向导端点暴露 | 待确认 | E-0003, E-0004 |

## 经验笔记

- 端到端验证应优先检验 `pents`、模板和正式 skill 是否能协同工作，而不是追求高风险攻击效果。
- 压缩 JS 文件的静态分析效率很高，grep 正则提取是关键手段。
- 对于 AI API 代理平台，管理后台是最大攻击面。
- 安装向导类端点是静态分析中最容易发现的高价值漏洞候选。
- crt.sh 无结果提示域名可能较新——建议数周后复查。
- 3 个正式 skill（javascript-analysis、api-discovery、subdomain-enumeration）均可有效指导工作，但 skill 间联动（如 JS 分析→API 发现）缺少正式衔接。
- 第一轮信息收集缺少 recon 基本盘，应把子域名、端口、CDN、源站线索和服务指纹作为主动验证前的固定检查项。

## 待确认问题

- ~~Claude Code 执行前确认授权窗口和允许的请求速率。~~ → 静态分析阶段无需确认
- HTTP、端口、路径/API 和漏洞验证前仍需确认授权窗口和允许请求速率。
- 是否允许把 `ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`、`st.devnu11.cn` 作为下一轮低频 HTTP 候选入口。
- 如需认证测试，需由用户提供测试账号并明确账号权限。
- Claude Code 已按 T-0042 完成正式主动 DNS 复测；HTTP/CDN、端口和服务指纹仍需 HTTP 授权窗口和速率。
- 数周后复查 crt.sh 证书透明日志。
