---
name: browser-test-agent
description: 使用 agent-browser 在授权范围内执行浏览器交互验证，并在需要视觉判断时自动调用 vision-reviewer 子代理。
category: recon
source: project
tags:
  - 浏览器测试
  - 信息收集
  - 证据采集
  - 子代理协作
required_tools:
  - agent-browser
---

# Browser Test Agent

## 适用场景

- 已确认 Web 入口在授权范围内，需要像真人一样打开页面、观察 UI、点击导航、填写低风险表单或保存截图。
- 需要确认登录页、注册页、搜索框、上传入口、OAuth、支付、管理后台等交互点是否存在。
- 需要把页面快照、截图、关键请求摘要和交互步骤回填到 `inventory.md`、`evidence.md`、入口卡片和 run 文档。
- 主模型是纯文本模型，但任务中可能出现验证码、Turnstile、canvas、图片化页面或截图脱敏判断。

## 授权边界

- 只访问 `scope.md` 和任务卡明确允许的目标。
- 默认允许：打开公开页面、读取可访问文本、执行 `agent-browser snapshot`、保存截图、记录低频网络摘要。
- 需要额外确认：登录、注册、提交表单、上传文件、OAuth 授权、支付流程、管理员入口、跨域跳转、源站 IP 直连。
- 禁止：暴力破解、凭据填充、绕过验证码、绕过风控、漏洞 payload 扫描、目录大字典爆破、真实支付、删除或破坏性写入。
- Claude Code 不操作 ai-board；ai-board 只由 Codex / 项目开发者维护。

## 工具硬约束

- `agent-browser` 是浏览器打开、页面快照、截图和浏览器交互的唯一允许链路。
- 如果 `agent-browser` 不存在、不可调用、缺少浏览器会话能力，或关键动作失败，立即停止并记录 blocker：`tool_missing_or_unavailable`。
- 禁止把 `WebFetch`、`Invoke-WebRequest`、`curl`、`wget`、Edge / Chrome / Chromium headless、Playwright、Puppeteer、Selenium 或任意现场安装的截图库当作替代链路。
- 禁止为了完成浏览器任务临时安装 Playwright、Puppeteer、Selenium、浏览器内核或截图工具。
- HTTP 抓取结果不能替代 `agent-browser snapshot`；系统浏览器截图不能替代 `agent-browser screenshot`。

## 前置条件

- 已读取 `scope.md`、`inventory.md`、相关入口卡片、当前 run 的 `brief.md` 和 `docs/项目路线/browser-test-agent流程.md`。
- 本机可运行 `agent-browser skills get core`，并已理解 `open -> snapshot -i -> act -> wait -> snapshot -i` 的循环。
- 已准备 run 目录下的 `outputs/browser/screenshots/`、`outputs/browser/snapshots/`、`outputs/browser/network-summary.md` 和 `raw/browser/`。
- 如果需要视觉判断，项目应提供或生成 `vision-reviewer` 子代理定义；推荐 `model: haiku`，但必须以实际 canary 结果确认该映射模型是否支持图片输入。

## 执行步骤

### 步骤 1：进入安全浏览器循环

1. 使用 `agent-browser open <url>` 打开任务卡允许的入口。
2. 立即执行 `agent-browser snapshot -i`，保存页面标题、URL、主要可交互元素。
3. 如果 `snapshot -i` 为空、交互元素过少或明显缺少页面主体，先执行 `agent-browser snapshot --full` 并保存证据。
4. 保存首屏截图到 run 目录。
5. 页面变化后必须重新 snapshot，不复用旧的 `@eN` 引用。
6. 点击、提交或 SPA 跳转后使用明确等待：URL、文本、元素或 `networkidle`。

### 步骤 2：优先用文本证据判断

主 agent 优先使用以下信息完成判断：

- `snapshot -i` 中的 heading、form、input、button、link、placeholder、label。
- 当前 URL、页面标题、状态码、跳转链。
- 网络请求列表和关键请求摘要。
- 可见文本、表单字段、按钮文案和错误提示。

如果这些信息足够判断页面状态，不调用视觉子代理。

### 步骤 3：自动判断是否需要 vision-reviewer

出现以下任一情况，主 agent 应主动调用 `vision-reviewer`，不等待用户提醒：

- `snapshot` 信息为空、过少，或页面主体疑似 canvas、图片、SVG、视频、WebGL 渲染。
- 页面存在验证码、Cloudflare Turnstile、滑块、二维码、图形验证码或 WAF 挑战状态，需要判断是否出现。
- 截图中可能包含敏感信息，需要确认是否需要打码。
- UI 布局、遮挡、弹窗、按钮可见性、标注截图是否准确，无法仅凭文本判断。
- `agent-browser screenshot --annotate` 产物需要确认编号、框选或标签是否遮挡关键内容。

触发视觉判断前，必须先做文本回退：`snapshot -i` 为空时先尝试 `snapshot --full`。如果 `snapshot --full` 已能说明页面状态，优先使用文本证据，并把未调用视觉子代理的原因写入 run 记录。

调用时只给 `vision-reviewer` 一个窄问题，例如：

```text
请只查看这张截图，判断页面是否出现验证码或 Turnstile。不要推测漏洞，不要访问网络。
```

### 步骤 4：处理视觉子代理结果

- 如果 `vision-reviewer` 返回 `can_read_image=false`，记录 blocker：`model_no_image_input`，不要猜测截图内容。
- 如果视觉结果与 snapshot 冲突，优先记录不确定点，必要时重新截图或停止。
- 如果视觉结果提示验证码、风控或 WAF 挑战，不尝试绕过，按停止条件处理。
- 视觉结果只能作为页面状态或证据质量判断，不能单独确认漏洞。

### 步骤 5：回填项目记录

- `evidence.md`：登记截图、浏览器交互证据、网络摘要和视觉复核 JSON。
- `asset-cards/AC-xxxx.md`：更新存活状态、登录/注册、CDN/WAF、交互点、截图和下一步。
- run `progress.md`：记录动作、等待条件、结果、阻塞原因和用时。
- run `Rxxx-report-delta.md`：只写本轮增量，不覆盖总报告。
- run `review.md`：记录 skill、CLI、tools、模型能力和任务卡改进建议。

## 停止条件

- 目标跳转到范围外资产。
- 需要账号、管理员权限、OAuth、支付、上传、写入或提交表单，但任务卡未授权。
- 出现验证码、Turnstile、风控升级、频繁 429/403、连续 5xx 或明显业务异常。
- 响应或截图包含敏感数据、凭据、个人信息或生产数据。
- `vision-reviewer` 不能读取图片，而当前判断必须依赖视觉内容。
- 任务目标是外部第三方站点，但没有明确授权，仅能记录待授权 blocker。

## 输出格式

```json
{
  "tested_targets": [],
  "browser_sessions": [],
  "screenshots": [],
  "snapshots": [],
  "key_requests": [],
  "visual_reviews": [],
  "updated_asset_cards": [],
  "potential_findings": [],
  "confirmed_findings": [],
  "blocked_or_skipped": [],
  "evidence_refs": [],
  "next_steps": [],
  "scope_risks": []
}
```

## 验收标准

1. 已按 `agent-browser` 快照循环完成页面观察，并保存截图或明确记录无法截图原因。
2. 已判断是否需要视觉子代理；触发或未触发的原因写入 run 记录。
3. 如调用 `vision-reviewer`，已保存结构化输出，并在不能读图时记录 blocker。
4. 已回填入口卡片、evidence、progress、report-delta 和 review 中与本轮有关的内容。
5. 未越过授权边界，未尝试绕过验证码或风控，未把视觉猜测写成 confirmed finding。
