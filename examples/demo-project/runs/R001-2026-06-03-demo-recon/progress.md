# Run 进度

## 元数据

- 项目：demo-project
- Run：R001-2026-06-03-demo-recon
- 阶段：recon
- 更新时间：2026-06-03 18:40:00

## 执行记录

| 时间 | 执行者 | 动作 | 状态 | 输出 |
| --- | --- | --- | --- | --- |
| 2026-06-03 18:31:00 | demo-agent | 读取 scope | 已执行 | 禁止端口扫描和源站直连 |
| 2026-06-03 18:33:00 | demo-agent | 生成 active-dns plan | 已执行 | outputs/active-dns-plan.md |
| 2026-06-03 18:36:00 | demo-agent | JS 静态线索整理 | 已执行 | outputs/static-js-summary.md |
| 2026-06-03 18:39:00 | demo-agent | 记录候选 finding | 已执行 | F-0001 |

## 阻塞 / 跳过

| 测试面 | 状态 | 原因类型 | 说明 |
| --- | --- | --- | --- |
| HTTP 探测 | 阻塞 | 授权缺失 | demo 不执行真实请求 |
| 端口扫描 | 不适用 | 范围外 | scope 禁止 |

## 待归并事实

- `app.example.test` 和 `api.example.test` 作为示例资产写入 inventory。
- `/api/v1/debug/status` 仅为 JS 静态线索，finding 保持 candidate。
