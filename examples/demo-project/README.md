# demo-project

这是一个安全的示例项目，用来展示 Pentest Framework 的项目记录结构。

示例目标全部使用保留域名 `example.test`，不代表真实资产，也不包含真实凭据、敏感响应或可执行攻击结果。

## 你可以从这里看什么

- `scope.md`：授权范围、禁止动作、速率和账号状态。
- `inventory.md`：资产、URL、API、参数、账号和测试面。
- `evidence.md`：证据编号、来源、hash 和证据链状态。
- `findings/F-0001.md`：候选 finding 的写法。
- `report.md`：报告汇总和证据缺口。
- `review.md`：复盘如何反馈到 skill、字典和流程。
- `runs/R001-2026-06-03-demo-recon/`：一次独立 run 的 brief、进度、证据、报告增量和复盘。

## 示例约束

- 只展示被动 recon、主动 DNS 计划和低频 HTTP 探测的记录方式。
- 不包含真实扫描输出。
- 不包含破坏性操作、认证爆破、漏洞利用或越界测试。
