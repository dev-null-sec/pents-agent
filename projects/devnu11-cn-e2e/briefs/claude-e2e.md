# Claude Code 端到端验证任务卡

## 任务

- 任务来源：ai-board `T-0008`
- 项目目录：`projects/devnu11-cn-e2e/`
- 授权目标：`*.devnu11.cn`
- 执行主体：Claude Code
- Codex 角色：仅准备 scope 和交接材料，不代跑测试

## 授权摘要

用户声明 `*.devnu11.cn` 是其自己的域名和服务器，允许进行授权测试。

执行前必须先读取并确认：

- `scope.md`
- `inventory.md`
- `evidence.md`
- `CLAUDE.md`
- `docs/项目路线/pents与子代理协作路线.md`

## 禁止动作

- DoS / DDoS / 压测 / 大流量扫描
- 破坏性写入、删除数据、持久化后门
- 社会工程学、钓鱼、凭据填充
- 测试非 `devnu11.cn` 及其子域名的第三方资产
- 未确认授权窗口和速率前进行主动爆破

## 建议流程

1. 使用 `pents scope devnu11-cn-e2e` 复核授权范围。
2. 选择至少 3 个正式 skill：
   - `skills/recon/subdomain-enumeration/SKILL.md`
   - `skills/recon/javascript-analysis/SKILL.md`
   - `skills/recon/api-discovery/SKILL.md`
   - 可根据发现结果补充 Web/API skill。
3. 将发现的资产写入 `inventory.md`。
4. 将证据写入 `evidence.md`。
5. 如发现漏洞，使用 `pents finding` 创建正式 finding；如未确认漏洞，记录候选 finding。
6. 使用 `pents report` 生成报告草稿。
7. 补写 `review.md`，记录 skill 是否好用、证据缺口和 CLI 改进建议。

## 输出要求

端到端验证完成后，项目目录至少应包含：

- 完整 `scope.md`
- 更新后的 `progress.md`
- 更新后的 `inventory.md`
- 更新后的 `evidence.md`
- 至少 1 个 finding 或候选 finding
- `report.md`
- `review.md`

## 停止条件

- 疑似越界
- 触发 WAF/IDS 或服务异常
- 需要高风险动作才能继续
- 需要测试账号或更高授权

