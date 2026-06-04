请执行端到端靶场验证任务。历史任务编号 `T-0008` 仅作为背景引用；不要操作 ai-board。

重要边界：

- 你是执行主体 Claude Code。
- Codex 只准备了 scope 和交接材料，没有对目标发起探测。
- 授权目标是 `*.devnu11.cn`。
- 用户声明这是自己的域名和服务器，允许授权测试。
- 禁止 DoS / DDoS / 压测 / 大流量扫描、破坏性操作、社工钓鱼、持久化、越权第三方目标。

执行前必须读取：

- `AGENTS.md`
- `CLAUDE.md`
- `docs/当前状态.md`
- `projects/devnu11-cn-e2e/scope.md`
- `projects/devnu11-cn-e2e/briefs/claude-e2e.md`
- `skills/README.md`

请使用项目已有 `pents` CLI 和正式 skill 完成端到端验证：

- `uv run --project cli pents scope devnu11-cn-e2e`
- 根据 `projects/devnu11-cn-e2e/briefs/claude-e2e.md` 至少调用 3 个正式 skill。
- 将资产、证据、候选 finding 或正式 finding、报告、复盘写入 `projects/devnu11-cn-e2e/`。

验收要求：

- 产出完整 `scope.md`、`progress.md`、`inventory.md`、`evidence.md`
- 至少 1 个 finding 或候选 finding
- 产出 `report.md`
- 产出 `review.md`
- 记录至少 3 个正式 skill 的调用结果、证据引用和发现结论

结束时：

- 只回填 `projects/devnu11-cn-e2e/` 下的 progress、inventory、evidence、report、review 等项目记录。
- 不运行 ai-board 命令；ai-board 验收和归档由 Codex / 项目开发者处理。
- 如果因为授权窗口、请求速率、账号或外部条件无法继续，不要擅自扩大测试；请记录 blocker 并停止。
