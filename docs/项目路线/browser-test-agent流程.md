# browser-test-agent 流程

## 目标

browser-test-agent 负责把“像真人一样使用 Web 应用”的测试动作标准化：打开页面、观察 UI、登录/注册、填写表单、导航、截图、记录关键请求响应，并把结果回填到入口卡片、证据、progress、report-delta 和 finding 候选。

它不是扫描器，也不替代漏洞判断。它的价值是让 Claude Code 能在授权范围内稳定完成交互式验证，并留下可复盘证据。

## 角色边界

| 角色 | 职责 |
| --- | --- |
| Codex | 维护 ai-board、任务卡、模板、验收和归档，不代替 Claude Code 执行真实目标浏览器测试 |
| Claude Code | 执行 browser-test-agent 任务卡，调用 agent-browser，回填项目记录 |
| agent-browser | 浏览器执行器：打开页面、快照、点击、填写、截图、保存状态、记录网络证据 |
| pents vision-review | 视觉复核 CLI：读取本地截图，调用外部 vision API，输出结构化 JSON |
| vision-reviewer | 可选对比子代理：仅在模型链路 canary 或任务卡明确要求时使用 |
| pents | 项目记录辅助：创建 run、登记 evidence、合并结构化输出、生成报告草稿 |

Claude Code 不操作 ai-board。ai-board 仍由 Codex / 项目开发者维护。

## 模型能力分层

browser-test-agent 默认按纯文本主 agent 设计。主 agent 应优先使用 `agent-browser snapshot`、DOM 文本、URL、网络摘要和请求/响应证据完成判断；截图默认作为证据保存，不要求主 agent 直接看图。

当页面状态必须依赖视觉判断时，主 agent 应主动调用 `pents vision-review`，而不是等待用户在任务卡中额外提醒。这样主流程只消费结构化 JSON，不依赖 Claude Code 内置子代理是否能稳定读取图片。

| 能力 | 默认执行者 | 说明 |
| --- | --- | --- |
| 页面导航、点击、填表、等待 | browser-test-agent | 基于 snapshot refs、语义 locator 和明确 wait |
| 页面结构、按钮、输入框、文本判断 | browser-test-agent | 优先用 accessibility snapshot 和可见文本 |
| 截图保存和证据路径登记 | browser-test-agent | 截图是证据，不等同于视觉判断 |
| 验证码、Turnstile、canvas、图片化页面、遮挡、脱敏 | pents vision-review | 只回答窄问题，输出结构化 JSON |
| 漏洞确认 | 主代理 / 授权测试流程 | 视觉结果不能单独确认漏洞 |

## 适用场景

- HTTP/CDN 存活后，需要确认页面结构、登录/注册入口和交互点。
- JS 静态分析发现 API、隐藏路径、setup、admin、OAuth、支付等候选，需要在页面上确认是否可达。
- 需要截图、表单状态、跳转链、关键请求/响应摘要作为证据。
- 需要认证后测试，但用户已提供测试账号或确认允许注册。
- 需要多账号权限测试，且用户明确提供对应账号和权限边界。

## 不适用 / 禁止

- 未授权目标。
- 暴力破解、凭据填充、撞库。
- 绕过验证码、绕过风控或规避检测。
- 真实支付、真实下单、破坏性写入、删除数据。
- 大字典目录爆破、漏洞 payload 扫描。
- 未确认授权前访问源站 IP 或第三方跳转目标。

## 输入要求

执行前至少读取：

- `scope.md`
- `inventory.md`
- 相关入口卡片 `asset-cards/AC-xxxx.md`
- `evidence.md`
- 当前 run 的 `brief.md`
- 相关 skill 或项目路线文档

如果需要登录、注册、管理员权限、OAuth 或支付流程，必须先确认账号、角色、允许动作和停止条件。凭据不得写入任务卡正文、shell 历史或报告。

## agent-browser 使用规则

核心循环：

```text
open -> snapshot -i -> act -> wait -> snapshot -i -> evidence
```

执行要求：

- 页面变化后必须重新 snapshot，不能复用旧的 `@eN` 引用。
- 优先使用 snapshot refs，其次用 role/text/label/placeholder，CSS 选择器只作 fallback。
- 页面变化后使用明确等待：URL、文本、元素或 networkidle，不默认硬等。
- 登录凭据优先使用 agent-browser auth vault 或 state 文件，不把密码写入命令历史。
- 每个关键页面保存截图；必要时保存 HAR 或网络请求摘要。
- 截图原图和标注图分开保存；标注图只用于报告，原图保留证据链。
- 多用户流程必须使用隔离 session，并记录账号角色和授权状态。

## 视觉复核 fallback

主 agent 在以下场景应自动调用 `pents vision-review`：

- `snapshot` 为空、信息过少，或页面主体疑似 canvas、图片、SVG、视频、WebGL。
- 页面出现验证码、Cloudflare Turnstile、滑块、二维码、图形验证、WAF 挑战或风控提示。
- 需要判断按钮、输入框、弹窗、遮挡层、错误页或登录页是否真的可见。
- 需要确认截图是否包含敏感信息，是否需要打码。
- 使用 `agent-browser screenshot --annotate` 后，需要确认编号、框选、箭头或标签是否遮挡关键 UI。

调用原则：

- 给 `pents vision-review` 的问题必须窄，例如“这张截图里是否出现 Turnstile？”。
- 只传截图路径、问题和必要上下文；CLI 只读取本地图片并调用视觉 API，不操作浏览器。
- API key 只允许通过环境变量读取，例如 `PENTS_VISION_API_KEY`；不得写入任务卡、shell 历史、报告或截图目录。
- 视觉模型通过 `PENTS_VISION_MODEL` 或 `--model` 指定；OpenAI-compatible base URL 通过 `PENTS_VISION_BASE_URL` 或 `--base-url` 指定。
- token 上限字段默认使用 `max_tokens`；官方 MiMo API 示例使用 `max_completion_tokens`，可通过 `--token-param max_completion_tokens` 或 `PENTS_VISION_TOKEN_PARAM=max_completion_tokens` 指定。CLI 在 base URL 为 `api.xiaomimimo.com` 时会自动使用 `max_completion_tokens`。
- 如果 CLI 返回 `missing_api_key`、`missing_model`、`api_timeout_or_network_error`、`can_read_image=false` 或其他错误，记录 blocker，不猜测图片内容。
- Claude Code 内置 `vision-reviewer` 子代理只作为可选对比链路，不再作为默认视觉主链路。
- 视觉判断只用于页面状态和证据质量复核，不直接写 confirmed finding。

调用示例：

```text
uv run --project cli pents vision-review runs/Rxxx/outputs/browser/screenshots/page.png --question "这张截图里是否出现验证码或 Turnstile？" --out runs/Rxxx/outputs/browser/visual-reviews/page.json
```

## 证据流

browser-test-agent 每轮至少生成：

| 证据类型 | 文件建议 | 说明 |
| --- | --- | --- |
| 页面截图 | `runs/Rxxx/outputs/browser/screenshots/*.png` | 登录页、关键页面、错误页、候选漏洞页面 |
| 交互步骤 | `runs/Rxxx/outputs/browser/steps.md` | 每一步动作、等待条件、结果 |
| 页面快照 | `runs/Rxxx/outputs/browser/snapshots/*.txt` | agent-browser snapshot 摘要，保留关键 refs 和 URL |
| 网络摘要 | `runs/Rxxx/outputs/browser/network-summary.md` | 关键请求/响应摘要，不保存敏感数据 |
| 视觉复核 | `runs/Rxxx/outputs/browser/visual-reviews/*.json` | `pents vision-review` 对截图的结构化判断 |
| HAR | `runs/Rxxx/raw/browser/*.har` | 仅在需要时保存，注意脱敏 |
| 状态文件 | `runs/Rxxx/raw/browser/state-*.json` | 仅保存测试账号状态，不提交真实敏感会话 |

证据登记到 `evidence.md` 时，备注建议包含：

```text
browser_step=...; source_url=...; screenshot=...; request=...; response=...; collected_at=...; chain=complete
```

## 入口卡片回填

browser-test-agent 必须更新或建议更新入口卡片：

- 存活状态：alive、redirect、blocked、dead、unknown。
- 登录 / 注册：有、无、未知、需账号。
- CDN/WAF：Cloudflare、Turnstile、验证码、WAF 拦截等。
- 交互点：登录、注册、搜索、上传、支付、OAuth、管理功能。
- API / 路径：页面实际触发或可见的接口。
- 风险线索：候选风险，不等同于 confirmed finding。
- 证据：截图、网络摘要、请求响应引用。
- 下一步：需要哪个 agent、skill、账号或授权。

如果入口卡片不存在，先创建 `projects/<name>/asset-cards/AC-xxxx.md`，再在 `inventory.md` 入口卡片索引中补一行。

## Finding 候选规则

只在满足以下条件时生成 finding 候选：

- 有明确目标和复现路径。
- 有截图或请求/响应证据。
- 能说明影响或潜在影响。
- 没有越过授权边界。
- 证据不足时状态只能是 `待确认` 或 `candidate`。

禁止因为页面看起来“像有漏洞”就写 confirmed。

## 停止条件

遇到以下情况停止对应流程并记录 blocker：

- 目标跳转到范围外资产。
- 需要真实支付、真实下单、破坏性写入或管理员权限，而未获授权。
- 出现敏感数据、凭据、个人信息或生产数据。
- WAF/验证码升级、频繁 429/403、连续 5xx 或明显业务异常。
- 需要绕过验证码、绕过风控或规避检测。
- 登录失败次数达到任务卡预算。

## 输出结构

Claude Code 返回给主代理的结构化输出至少包含：

- tested_targets
- browser_sessions
- screenshots
- snapshots
- key_requests
- visual_reviews
- updated_asset_cards
- potential_findings
- confirmed_findings
- blocked_or_skipped
- evidence_refs
- next_steps
- scope_risks

## 与后续任务关系

- T-0022：低频 HTTP/CDN 验证后，如果发现页面入口，可用本流程继续浏览器交互验证。
- T-0052：入口卡片是 browser-test-agent 的主要回填对象。
- T-0054：源站线索、第三方跳转和 IP 直连边界由源站分级策略约束。
- pentest-intel-hub：浏览器测试经验可以沉淀到 `knowledge/cards/browser-testing/`。
