# Claude Code 任务卡：T-0058 / hiwonder R002 视觉 Canary

## 给用户的短提示

```text
读取 projects/hiwonder-cn-canary/briefs/claude-t0058-mimo-vision-canary.md 执行；不要操作 ai-board。严格使用 agent-browser 截图，使用 pents vision-review 做图片识别；任一工具不可用就记录 blocker 并停止，不得使用 Playwright/Puppeteer/Edge/Chrome/WebFetch 或内置视觉子代理等替代链路，不得安装工具。
```

## 任务目标

- 项目：`projects/hiwonder-cn-canary/`
- 任务编号：`T-0058`
- 本轮 run：`projects/hiwonder-cn-canary/runs/R002-2026-06-04-mimo-vision-canary/`
- 目标 URL：`https://www.hiwonder.com.cn/admin_hiwonder.php/`
- 执行主体：Claude Code
- 浏览器执行器：`agent-browser`
- 视觉复核主链路：`uv run --project cli pents vision-review`
- 视觉 API 模型：`mimo-v2.5`

本轮只验证浏览器截图和视觉识别链路：公开页面打开、页面快照、截图、`pents vision-review` 读图 canary、结果回填。

## 工具硬约束

`agent-browser` 是本任务唯一允许的浏览器、页面快照和截图链路。

执行前先确认 `agent-browser` 可用，例如读取 `agent-browser skills get core` 或运行项目环境中已有的离线/快速自检命令。若 `agent-browser` 命令不存在、不可调用、缺少浏览器会话能力，或 open/snapshot/screenshot 任一步无法执行，应立即停止并记录 blocker：`tool_missing_or_unavailable`。

禁止把以下工具当作替代浏览器或替代截图链路：

- `WebFetch`、`Invoke-WebRequest`、`curl`、`wget`
- Edge / Chrome / Chromium headless
- Playwright、Puppeteer、Selenium
- 任意现场安装的截图库、浏览器自动化库或完整浏览器包

禁止为了完成本任务安装工具、安装浏览器、安装 Playwright 浏览器内核，或把 HTTP 抓取结果当作浏览器 snapshot。

## 授权边界

允许：

- 打开任务目标 URL。
- 执行 `agent-browser snapshot -i`。
- 若 `snapshot -i` 为空或交互元素过少，先执行 `agent-browser snapshot --full`。
- 保存首屏截图。
- 调用 `pents vision-review` 读取截图，判断视觉 API 是否能读图。
- 回填本轮 run 文档。

禁止：

- 登录、注册、提交表单、点击验证码或尝试绕过验证组件。
- payload、爆破、漏洞扫描、目录扫描、扩展路径测试。
- 修改或覆盖 `R001-2026-06-04-vision-canary/` 的任何文件。
- 操作 ai-board；ai-board 只由 Codex / 项目开发者维护。

## 执行步骤

1. 读取 `projects/hiwonder-cn-canary/scope.md`。
2. 读取 R001 记录作为基线，但不要修改 R001：
   - `projects/hiwonder-cn-canary/runs/R001-2026-06-04-vision-canary/progress.md`
   - `projects/hiwonder-cn-canary/runs/R001-2026-06-04-vision-canary/evidence.md`
   - `projects/hiwonder-cn-canary/runs/R001-2026-06-04-vision-canary/R001-report-delta.md`
   - `projects/hiwonder-cn-canary/runs/R001-2026-06-04-vision-canary/review.md`
3. 创建或进入 `projects/hiwonder-cn-canary/runs/R002-2026-06-04-mimo-vision-canary/`。
4. 准备目录：
   - `outputs/browser/screenshots/`
   - `outputs/browser/snapshots/`
   - `outputs/browser/visual-reviews/`
   - `raw/browser/`
5. 使用 `agent-browser open https://www.hiwonder.com.cn/admin_hiwonder.php/` 打开页面。
6. 使用 `agent-browser snapshot -i` 保存交互快照到 `outputs/browser/snapshots/`。
7. 如果交互快照为空或过少，执行 `agent-browser snapshot --full` 并保存。
8. 使用 `agent-browser screenshot` 保存截图到 `outputs/browser/screenshots/`。
9. 调用 `pents vision-review`，模型使用 `mimo-v2.5`，并明确记录 `vision_model=mimo-v2.5`。
10. 保存视觉复核 JSON 到 `outputs/browser/visual-reviews/`。
11. 回填本轮文档。

调用示例：

```text
uv run --project cli pents vision-review projects/hiwonder-cn-canary/runs/R002-2026-06-04-mimo-vision-canary/outputs/browser/screenshots/admin_hiwonder_2026-06-04.png --question "判断截图里是否出现登录页、验证码/滑块/WAF 挑战、可见交互元素和敏感信息" --out projects/hiwonder-cn-canary/runs/R002-2026-06-04-mimo-vision-canary/outputs/browser/visual-reviews/vision-review-001.json
```

API key 只允许通过本地 `.env` / `.env.local` 或环境变量读取，例如：

```text
PENTS_VISION_API_KEY=<本地填写>
PENTS_VISION_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
PENTS_VISION_MODEL=mimo-v2.5
```

不得把 key 写进任务卡、命令历史、日志或报告。真实 `.env` 不入 git；仓库只保留 `.env.example`。

如果 CLI 返回 `missing_api_key`、`missing_model`、`api_timeout_or_network_error` 或其他错误，记录 blocker 并停止视觉判断，不要改用 Claude Code 内置视觉子代理反复尝试。

## pents vision-review 输出要求

视觉复核只回答图片可读性和页面可见状态，不推测漏洞，不访问网络。

保存结构化 JSON，至少包含：

```json
{
  "model": "mimo-v2.5",
  "can_read_image": false,
  "blocker": "",
  "page_type": "",
  "captcha_or_waf": {
    "present": null,
    "type": "",
    "evidence": ""
  },
  "visible_interactive_elements": [],
  "sensitive_content": {
    "present": null,
    "description": ""
  },
  "confidence": "low"
}
```

如果视觉 API 仍不能读取图片，写：

- `can_read_image=false`
- `blocker=<具体原因>`
- 不要猜测截图内容。

## 回填文件

本轮至少写入：

- `projects/hiwonder-cn-canary/runs/R002-2026-06-04-mimo-vision-canary/progress.md`
- `projects/hiwonder-cn-canary/runs/R002-2026-06-04-mimo-vision-canary/evidence.md`
- `projects/hiwonder-cn-canary/runs/R002-2026-06-04-mimo-vision-canary/R002-report-delta.md`
- `projects/hiwonder-cn-canary/runs/R002-2026-06-04-mimo-vision-canary/review.md`

如果任务因 `agent-browser` 不可用停止，也必须写入以上文档，说明停止点、原因、影响和下一步建议。

## 成功标准

- 未覆盖 R001。
- 未操作 ai-board。
- 未登录、未提交表单、未绕过验证码、未做漏洞测试。
- 全程使用 `agent-browser` 完成浏览器动作；若不可用，已停止并记录 blocker。
- 已记录 `vision_model=mimo-v2.5` 和 `vision_canary_status`。
- 已明确判断视觉 API 是否具备图片输入能力。
