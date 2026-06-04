# Browser Test Agent 任务卡

## 给用户的短提示

```text
读取本任务卡，按 browser-test-agent 流程执行；不要操作 ai-board。
```

## 任务分配

- 项目：{{project_name}}
- 任务编号：{{task_id}}
- 执行主体：Claude Code
- 浏览器执行器：agent-browser
- 创建时间：{{created_at}}
- 当前状态：planned

## 授权范围摘要

### 可测试入口

{{in_scope_entries}}

### 不在范围内

{{out_of_scope_items}}

### 禁止动作

{{forbidden_items}}

### 停止条件

{{stop_items}}

## 输入材料

| 类型 | 路径 | 备注 |
| --- | --- | --- |
| scope | `scope.md` | 授权范围和禁止动作 |
| inventory | `inventory.md` | 资产和入口卡片索引 |
| asset-card | {{asset_card_paths}} | 待测试入口卡片 |
| evidence | `evidence.md` | 证据编号和历史记录 |
| route-doc | `docs/项目路线/browser-test-agent流程.md` | 浏览器测试流程 |

## 账号与会话

- 是否需要登录：{{login_required}}
- 账号来源：{{account_source}}
- 账号角色：{{account_roles}}
- 凭据处理：不得写入任务卡正文、shell 历史、报告或截图；优先使用 agent-browser auth vault 或临时 state。
- 会话状态文件：{{session_state_path}}

## 建议流程

1. 创建或进入本轮 run 目录。
2. 准备 `outputs/browser/screenshots/`、`outputs/browser/snapshots/`、`outputs/browser/network-summary.md` 和 `raw/browser/`。
3. 使用 agent-browser 打开入口 URL。
4. 执行 `snapshot -i`，记录页面标题、URL、主要交互元素。
5. 保存首屏截图。
6. 识别登录、注册、搜索、上传、支付、OAuth、管理功能等交互点。
7. 如有授权账号，按账号角色登录并保存 state；登录后重新 snapshot。
8. 对任务卡指定的少量路径/API 候选做页面级验证。
9. 记录关键请求/响应摘要，避免保存敏感数据。
10. 更新入口卡片、inventory、evidence、progress、report-delta 和 review。

## agent-browser 操作规则

- 页面变化后重新 snapshot，不复用旧 refs。
- 优先使用 snapshot refs；role/text/label/placeholder 次之；CSS selector 只作 fallback。
- 每次点击、提交或 SPA 跳转后使用明确 wait。
- 截图保存到 run 目录，不覆盖旧截图。
- 如保存 HAR 或 state，必须记录脱敏要求。
- 结束后关闭不需要的浏览器 session，或说明保留原因。

## 证据要求

| 证据 | 要求 |
| --- | --- |
| 截图 | 关键页面、错误页、候选漏洞页面必须截图 |
| 交互步骤 | 写清动作、等待条件、结果和证据文件 |
| 页面快照 | 保存关键 snapshot 摘要 |
| 请求/响应 | 只保存关键摘要和脱敏后的引用 |
| 入口卡片 | 更新存活状态、交互点、风险线索和证据 |

## Finding 候选

只有在有复现路径和证据时才输出 finding 候选。证据不足时不得写 confirmed。

候选 finding 输出字段：

- 标题
- 影响入口
- 复现步骤
- 证据引用
- 影响判断
- 限制和不确定点
- 建议状态：candidate / 待确认 / confirmed

## 回填文件

- `runs/Rxxx/progress.md`
- `runs/Rxxx/evidence.md`
- `runs/Rxxx/Rxxx-report-delta.md`
- `runs/Rxxx/review.md`
- `inventory.md`
- `evidence.md`
- `progress.md`
- `report.md`
- `review.md`
- `asset-cards/AC-xxxx.md`

## 输出格式

```json
{
  "tested_targets": [],
  "browser_sessions": [],
  "screenshots": [],
  "key_requests": [],
  "updated_asset_cards": [],
  "potential_findings": [],
  "confirmed_findings": [],
  "blocked_or_skipped": [],
  "evidence_refs": [],
  "next_steps": [],
  "scope_risks": []
}
```
