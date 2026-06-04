# 主动 DNS 执行封装

## 定位

`pents active-dns` 是主动 DNS 流程的计划生成器和执行约束器，不是默认联网扫描器。

默认行为是根据 domain、字典、resolver、canary 和引擎选择生成一份可交给 Claude Code 执行的计划，并可保存到 run 的 `outputs/`。正式扫描仍由获得授权的执行者在对应任务卡中运行。

## 为什么默认不直接执行

- 主动 DNS 虽然不触发 HTTP 请求，但仍属于授权测试动作。
- devnu11 R001 暴露过 `dnsx -wd` 误用和 0 命中误判，必须把预检、枚举、复核拆开。
- 用户要求正式测试由 Claude Code 执行，Codex 负责工具链和流程前置准备。
- 不同环境下 resolver、shell、PATH 和第三方工具位置会影响结果，执行前应先把这些信息写进计划。

## 标准流程

1. 规范化目标：支持 `*.example.com`，实际枚举根域为 `example.com`。
2. 读取字典：默认使用 `dicts/curated/subdomains-main.txt`。
3. 写入 resolver 文件：保存在 run `outputs/active-dns-resolvers.txt`。
4. Canary 子域校验：至少提供 1 个已知存在子域，例如 `ai.example.com`。
5. 随机 NXDOMAIN 检查：用于发现泛解析或 wildcard。
6. 逐 resolver 自检：慢或 0 响应的 resolver 必须剔除。
7. 完整字典枚举：默认使用 `massdns direct`，先生成候选文件，再把候选文件作为 massdns 输入。
8. 命中提取：从 massdns `Snl` 输出中提取 A/AAAA/CNAME 命中的 host，生成 `raw/active-dns-hits.txt`。
9. 证据登记：生成 `pents evidence` 命令，把命中列表登记为 `active-dns` 证据。
10. 报告摘要：生成待回填摘要模板，执行后填写命中数量、剔除 resolver、wildcard 结论和证据编号。

`puredns`、`shuffledns` 和 `dnsx` 只保留为可选诊断或兼容替代，不再作为默认主动 DNS 执行链路。Claude Code 场景默认执行 `tools/recon/active-dns-massdns.ps1`，避免 wrapper 内部 stdin pipe 卡死。

## 禁止项

- 禁止把 `dnsx -wd` 当作常规枚举参数。
- 禁止 canary 未命中时继续跑完整字典。
- 禁止随机 NXDOMAIN 命中时直接把结果当真实子域。
- 禁止工具缺失时声称已执行主链路。
- 禁止 massdns direct 卡住后改回 puredns pipe 继续碰运气；应先检查候选文件、resolver 文件和 massdns 输入文件参数。
- 禁止把 HTTP 探测、端口扫描或漏洞验证混入主动 DNS 命令。

## 输出文件

保存模式下，命令会写入：

```text
projects/<name>/runs/<run>/outputs/active-dns-plan.md
projects/<name>/runs/<run>/outputs/active-dns-summary.md
projects/<name>/runs/<run>/outputs/active-dns-resolvers.txt
projects/<name>/runs/<run>/outputs/active-dns-canary-targets.txt
projects/<name>/runs/<run>/outputs/active-dns-nxdomain-targets.txt
projects/<name>/runs/<run>/outputs/active-dns-metrics.json
projects/<name>/runs/<run>/outputs/active-dns-summary.json
```

执行后原始结果应写入：

```text
projects/<name>/runs/<run>/raw/
projects/<name>/runs/<run>/raw/active-dns-candidates.txt
projects/<name>/runs/<run>/raw/active-dns-massdns.txt
projects/<name>/runs/<run>/raw/active-dns-hits.txt
```

这些 raw 输出默认不进入 Git。
