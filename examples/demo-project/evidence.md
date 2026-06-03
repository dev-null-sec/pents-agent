# 证据索引

## 元数据

- 项目：demo-project
- 更新时间：2026-06-03 18:40:00

## 证据列表

| 编号 | 类型 | 关联目标 | 关联漏洞 | 路径或引用 | 备注 |
| --- | --- | --- | --- | --- | --- |
| E-0001 | 备注 | demo-project |  | progress.md | 项目初始化；chain=complete |
| E-0002 | active-dns-plan | `*.example.test` |  | runs/R001-2026-06-03-demo-recon/outputs/active-dns-plan.md | source=demo; file=active-dns-plan.md; chain=complete |
| E-0003 | js-summary | `https://app.example.test` | F-0001 | runs/R001-2026-06-03-demo-recon/outputs/static-js-summary.md | source=demo-js; sha256=demo-only; chain=complete |
| E-0004 | request-summary | `/api/v1/debug/status` | F-0001 | requests/debug-status-redacted.txt | source_url=https://api.example.test/api/v1/debug/status; chain=incomplete |

## 请求证据

| 证据编号 | 方法 | URL 或端点 | 请求引用 | 响应引用 | 备注 |
| --- | --- | --- | --- | --- | --- |
| E-0004 | GET | `/api/v1/debug/status` | requests/debug-status-redacted.txt | responses/debug-status-redacted.txt | 示例脱敏引用，不包含真实响应 |

## 截图证据

| 证据编号 | 路径 | 关联步骤 | 备注 |
| --- | --- | --- | --- |
|  |  |  | 无 |

## 终端输出证据

| 证据编号 | 命令摘要 | 输出引用 | 备注 |
| --- | --- | --- | --- |
| E-0002 | pents active-dns 计划生成 | runs/R001-2026-06-03-demo-recon/outputs/active-dns-plan.md | 未执行真实扫描 |
