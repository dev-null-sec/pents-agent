# devnu11-cn-e2e runs

本目录用于记录 devnu11 项目的后续复测或专项测试轮次。

顶层文档保留累计事实：

- `scope.md`：授权范围和前置条件。
- `inventory.md`：累计资产、API、参数、账号、测试面。
- `evidence.md`：累计证据索引。
- `report.md`：当前总报告。
- `review.md`：项目级复盘。

每一轮新测试应单独建目录：

```text
runs/R001-2026-06-03-active-recon/
  brief.md
  progress.md
  evidence.md
  outputs/
  raw/
  R001-report-delta.md
  review.md
```

## 下一轮建议

下一轮主动验证建议命名为：

```text
runs/R001-<date>-active-recon/
```

进入该 run 前需要用户确认：

- 主动 DNS：授权窗口、DNS 并发/速率、resolver。
- HTTP / CDN / 服务指纹：实际访问 URL、授权窗口、HTTP 请求速率。
- API / 认证后测试：实际访问 URL、测试账号、管理员账号授权或注册许可。

本轮结束后，先写 `R001-report-delta.md`。如果后续还有第二次、第三次复测，继续使用 `R002-report-delta.md`、`R003-report-delta.md`，再由主代理决定哪些内容合并到顶层 `report.md`。
