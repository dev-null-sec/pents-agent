# R003 报告增量

## 元数据

- 项目：devnu11-cn-e2e
- Run：R003-2026-06-03-puredns-massdns-retest
- 执行时间：2026-06-04 11:05:36 ~ 11:06:36 CST
- 引擎：massdns direct
- 执行主体：Claude Code（T-0042 正式执行）

## 执行摘要

Claude Code 按 T-0042 任务卡正式执行了 `devnu11.cn` 主动 DNS 子域名枚举。

- **链路**：`massdns direct`（tools/recon/active-dns-massdns.ps1）
- **字典**：`dicts/curated/subdomains-main.txt`，167,377 词条
- **Resolver**：1.1.1.1, 1.0.0.1, 8.8.8.8, 8.8.4.4, 223.5.5.5, 119.29.29.29（6 个全通过自检）
- **总耗时**：60.669 秒
- **命中**：4（ai.devnu11.cn, blog.devnu11.cn, lk.devnu11.cn, st.devnu11.cn）
- **Canary**：ai.devnu11.cn 可解析 ✓
- **泛解析**：未发现 wildcard（随机 NXDOMAIN 检查通过）

## 与 R001 基线对比

| 指标 | R001 (Codex dnsx) | R003 (Claude Code massdns) | 差异 |
| --- | --- | --- | --- |
| 字典 | subdomains-main.txt, 167,377 | subdomains-main.txt, 167,377 | 一致 |
| 引擎 | dnsx (-a -aaaa -cname -json) | massdns (-t A, -o Snl) | 不同工具 |
| Resolver | 7 个（含 9.9.9.9） | 6 个（不含 9.9.9.9） | R003 少 9.9.9.9，pents 默认未包含 |
| 耗时 | ~99.363 秒 | 60.669 秒 | R003 快约 39% |
| 命中数 | 5 | 4 | online 仅在 R001 中出现 |
| 可解析子域 | ai, blog, lk, st | ai, blog, lk, st | 完全一致 |
| A 记录 | 均指向 Cloudflare | 均指向 Cloudflare | 一致 |
| online.devnu11.cn | NOERROR，无 A/AAAA | — | massdns 不记录 NODATA |

## 差异解释

`online.devnu11.cn` 未在 R003 命中中出现的原因是 massdns 的 `Snl` 输出格式只包含有 A/AAAA/CNAME 记录的行。该域名此前已被 E-0010 标记为 NODATA 候选，不作为 Web 入口，因此不构成遗漏。

## 结论

- Claude Code 正式主动 DNS 枚举已通过 T-0042 完成。
- `massdns direct` 链路可用、稳定、高效（60.669 秒完成 167K 词条）。
- 可解析子域名命中与 R001 Codex 基线完全一致，无遗漏。
- 未发现 wildcard / 泛解析噪声。
- 可解析的 4 个子域名均指向 Cloudflare 代理 IP，与 R001 E-0010 记录一致。
- HTTP/CDN、端口和服务指纹探测仍需 HTTP 授权窗口和速率确认后方可执行。
