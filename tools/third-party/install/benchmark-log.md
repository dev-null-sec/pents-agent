# 第三方工具 benchmark 记录

## 2026-06-03 devnu11 active DNS baseline

- 授权目标：`*.devnu11.cn`
- 字典：`dicts/curated/subdomains-main.txt`，167377 行
- 引擎：`puredns v2.1.1 + massdns v1.1.0`
- 复核：`dnsx v1.2.3`
- Resolver：`1.1.1.1`、`1.0.0.1`、`8.8.8.8`、`8.8.4.4`、`223.5.5.5`、`119.29.29.29`
- puredns rate limit：10000 qps
- 原始 benchmark 目录：`tools/third-party/cache/benchmarks/T-0046-devnu11-active-dns-20260603-r2/`（缓存目录，不进 Git）

| 步骤 | 耗时 |
| --- | ---: |
| canary dnsx | 2.881s |
| resolver 1.1.1.1 | 0.906s |
| resolver 1.0.0.1 | 0.915s |
| resolver 8.8.8.8 | 2.681s |
| resolver 8.8.4.4 | 2.718s |
| resolver 223.5.5.5 | 2.506s |
| resolver 119.29.29.29 | 0.695s |
| NXDOMAIN dnsx | 2.930s |
| puredns full bruteforce | 209.306s |
| dnsx verify retry=1 timeout=2 | 2.730s |
| dnsx verify retry=2 timeout=3 | 7.328s |

结果摘要：

- puredns 原始命中：3 条
- dnsx `retry=1 timeout=2` 复核：1 条，存在漏报
- dnsx `retry=2 timeout=3` 复核：3 条
- 可确认子域：`ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`
- 完整可靠链路耗时：235.596s

结论：

- `puredns + massdns` 主链路可在 5 分钟内跑完整个主字典。
- 最终复核不应沿用过紧的 `retry=1 timeout=2`；小列表复核默认采用 `retry=2 timeout=3` 更稳。
- 后续 Claude Code 复测需要记录各扫描步骤耗时，并与本 baseline 对比。
