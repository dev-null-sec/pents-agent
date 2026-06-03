# Run Brief

- 项目：demo-project
- Run：R001-2026-06-03-demo-recon
- 目标：展示信息收集、主动 DNS 计划、证据登记和候选 finding。
- 执行者：demo-agent
- 授权边界：只使用 `example.test` 保留域名，不执行真实扫描。

## 任务目标

1. 读取 scope，确认禁止动作。
2. 生成主动 DNS 执行计划样例。
3. 记录 JS 静态分析线索。
4. 将 `/api/v1/debug/status` 写成 candidate finding。
5. 回填 evidence、report-delta、review。

## 禁止动作

- 真实 HTTP 请求
- 端口扫描
- 源站直连
- 漏洞利用
