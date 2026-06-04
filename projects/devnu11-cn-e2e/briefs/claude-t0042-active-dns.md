# Claude Code 任务卡：T-0042 正式主动 DNS 枚举

## 一句话目标

由 Claude Code 正式执行 `devnu11.cn` 主动 DNS 子域名枚举，并与 R001 Codex 前置验证基线对比。

## 启动方式

在 Claude Code 中读取本任务卡和 scope 后执行。不要操作 ai-board；ai-board 的申领、验收和归档由 Codex / 项目开发者处理。

## 必读

- `docs/当前状态.md`
- `docs/项目路线/主动DNS执行封装.md`
- `projects/devnu11-cn-e2e/scope.md`
- `projects/devnu11-cn-e2e/runs/R001-2026-06-03-active-dns/review.md`
- `tools/recon/README.md`

## 边界

- 授权范围：`*.devnu11.cn`
- 本轮只做 DNS 子域名枚举和 DNS 记录复核。
- 禁止 HTTP 存活、端口扫描、路径/API 请求、漏洞验证、源站直连。
- R001 是 Codex 前置验证中误执行完整字典形成的对照基线，不是 Claude Code 正式结果。

## 执行要求

1. 使用 `pents active-dns --engine auto` 生成或复核执行计划，默认链路必须是 `massdns direct`。
2. 按计划运行 `tools/recon/active-dns-massdns.ps1`，不要回退到 `puredns bruteforce -b massdns`。
3. 脚本内置 canary、resolver 自检、NXDOMAIN/wildcard 检查、候选生成、完整枚举和命中提取；如果任一步失败，记录 blocker，不继续扩展到 HTTP 或端口。
4. canary 要求：
   - `ai.devnu11.cn` 应可解析。
   - 随机 3-5 个不存在子域应为 NXDOMAIN 或不可解析。
   - resolver 必须可用。
5. 使用 `dicts/curated/subdomains-main.txt` 完整枚举 `devnu11.cn`。
6. 对命中结果补查或分类 A/AAAA/CNAME，并区分：
   - 有 A/AAAA
   - NOERROR 但无 A/AAAA
   - NXDOMAIN
   - 疑似泛解析噪声

## 可参考参数

R001/T-0046 前置验证参数仅供对照，Claude Code 可按实际情况调整并记录原因。新的默认链路以 `massdns direct` 为准：

- 字典：`dicts/curated/subdomains-main.txt`
- canary：`ai.devnu11.cn`
- resolver：优先使用已验证可用的公共 resolver，剔除超时或 0 响应 resolver
- massdns hashmap size：默认 `10000`
- 必须记录每个扫描步骤的耗时、退出码、候选数和命中数

## 回填要求

更新：

- `projects/devnu11-cn-e2e/progress.md`
- `projects/devnu11-cn-e2e/inventory.md`
- `projects/devnu11-cn-e2e/evidence.md`
- `projects/devnu11-cn-e2e/report.md`
- `projects/devnu11-cn-e2e/review.md`
- 必要时创建新的 run 目录，如 `runs/R002-<date>-claude-active-dns/`

必须记录：

- 字典路径和词条数
- resolver
- 并发、retry、timeout
- 耗时
- canary 与泛解析检查结果
- 命中列表和 A/AAAA/CNAME 复核
- 与 R001 Codex 前置验证结果的差异

## 完成

完成后只回填上述项目文档和 run 文档，并在 review 中写清结论、耗时对比和遗留问题。不要运行 ai-board 命令；Codex 会根据回填结果验收和归档 T-0042。

如果缺工具、缺权限、resolver 不稳定或结果异常，先记录 blocker/复盘，不要扩展到 HTTP 或端口。
